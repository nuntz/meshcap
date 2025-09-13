import argparse
import sys
import time
import pickle
import logging
import threading
from datetime import datetime, timezone
import meshtastic.serial_interface
import meshtastic.tcp_interface
from pubsub import pub
from .filter import parse_filter, evaluate_filter, FilterError
from .payload_formatter import PayloadFormatter
from .identifiers import to_node_num, to_user_id, NodeBook
from . import constants

logger = logging.getLogger(__name__)


class MeshCap:
    """Main class for the Meshtastic packet capture application."""

    def __init__(self, args):
        """Initialize the MeshCap with parsed command line arguments.

        Args:
            args: Parsed arguments object from argparse
        """
        self.args = args
        self.packet_count = 0
        self.target_count = args.count
        self.write_file_handle = None
        self.filter_rpn = None
        self.should_exit = False
        # Cache NodeBook per MeshCap instance (initialized when connected)
        self.node_book: NodeBook | None = None
        # Initialize payload formatter
        self.payload_formatter = PayloadFormatter()
        # Thread synchronization lock for shared state
        self._lock = threading.Lock()

    def _format_hop_info(self, packet: dict) -> str:
        """Format hop information from a packet.

        Extracts hop_start and hop_limit (snake_case, with camelCase fallback for hopLimit)
        and returns a concise hop usage string.

        Logic:
        - If hop_start != 0 and hop_limit <= hop_start, show "Hops:<used>/<start>"
        - Otherwise, show "Hop:<hop_limit>"

        Args:
            packet (dict): The packet dictionary possibly containing hop values.

        Returns:
            str: Formatted hop information string.
        """
        hop_start = packet.get("hop_start", packet.get("hopStart", 0)) or 0
        hop_limit = packet.get("hop_limit", packet.get("hopLimit", 0)) or 0

        try:
            hs = int(hop_start)
        except (ValueError, TypeError):
            hs = 0
        try:
            hl = int(hop_limit)
        except (ValueError, TypeError):
            hl = 0

        # Show usage format only when both values are present and valid
        if hs != 0 and hl != 0 and hl <= hs:
            used = hs - hl
            return f"Hops:{used}/{hs}"
        else:
            return f"Hop:{hl}"

    def _format_flags(self, packet: dict) -> str:
        """Format active flag indicators from a packet.

        Checks for the following boolean fields on the packet dict:
        - wantAck -> 'A'
        - viaMqtt (protobuf field 'via_mqtt') -> 'M'

        Returns an empty string when no flags are active; otherwise returns
        a string with a leading space, followed by the active flags enclosed
        in brackets. The flag order is always 'A' then 'M'.

        Args:
            packet (dict): The packet dictionary to inspect.

        Returns:
            str: "", " [A]", " [M]", or " [AM]" depending on active flags.
        """
        flags: list[str] = []

        # 'A' flag for acknowledgements requested
        try:
            if bool(packet.get("wantAck", False)):
                flags.append("A")
        except TypeError:
            pass

        # 'M' flag for packets that came via MQTT (protobuf: via_mqtt)
        try:
            if bool(packet.get("viaMqtt", False)):
                flags.append("M")
        except TypeError:
            pass

        if not flags:
            return ""
        return f" [{''.join(flags)}]"

    def _on_packet_received(self, packet, interface, no_resolve=False, verbose=False):
        """Callback function for received packets.

        Args:
            packet: The received packet
            interface: The Meshtastic interface (can be None when reading from file)
            no_resolve (bool): If True, skip node name resolution
            verbose (bool): If True, show JSON details for unknown packet types
        """
        # Apply filter if specified
        if self.filter_rpn:
            try:
                if not evaluate_filter(self.filter_rpn, packet, interface):
                    logger.debug("Packet filtered out by filter expression")
                    return  # Packet doesn't match filter, skip processing
            except FilterError as e:
                logger.warning(f"Filter evaluation error: {e}")
                return

        # Write packet to file if writer is enabled (synchronized access)
        with self._lock:
            if self.write_file_handle:
                logger.debug(f"Writing packet to file: {type(packet)}")
                pickle.dump(packet, self.write_file_handle)

        # Format and print the packet (outside lock to minimize lock time)
        formatted = self._format_packet(packet, interface, no_resolve, verbose)
        print(formatted)

        # Update shared state under lock
        with self._lock:
            # Increment packet counter (only for matching packets)
            self.packet_count += 1
            current_count = self.packet_count

            # Check if we've reached the target count
            if self.target_count and current_count >= self.target_count:
                print(f"\nProcessed {current_count} matching packets. Exiting...")
                if self.write_file_handle:
                    self.write_file_handle.close()
                    self.write_file_handle = None
                self.should_exit = True

    def _read_packets_from_file(self, filename, no_resolve, verbose=False):
        """Read pickled packets from a file and process them.

        Args:
            filename (str): Path to the file containing pickled packets
            no_resolve (bool): If True, skip node name resolution
            verbose (bool): If True, show JSON details for unknown packet types
        """
        logger.info(f"Reading packets from file: {filename}")
        try:
            with open(filename, "rb") as f:
                while True:
                    try:
                        packet = pickle.load(f)
                        self._on_packet_received(packet, None, no_resolve, verbose)
                    except EOFError:
                        logger.debug("Reached end of file")
                        break
        except FileNotFoundError:
            logger.error(f"File not found: {filename}")
            print(f"Error: File '{filename}' not found", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            logger.error(f"Error reading from file '{filename}': {e}")
            print(f"Error reading from file '{filename}': {e}", file=sys.stderr)
            sys.exit(1)

    def run(self):
        """Run the main application logic."""
        # Parse filter expression if provided
        if self.args.filter:
            try:
                logger.info(f"Parsing filter expression: {' '.join(self.args.filter)}")
                self.filter_rpn = parse_filter(self.args.filter)
                print(f"Using filter: {' '.join(self.args.filter)}")
            except FilterError as e:
                logger.error(f"Invalid filter expression: {e}")
                print(f"Error: Invalid filter expression: {e}", file=sys.stderr)
                sys.exit(1)

        # Handle file reading mode
        if self.args.read_file:
            print(f"Reading packets from {self.args.read_file}...")
            self._read_packets_from_file(
                self.args.read_file, self.args.no_resolve, self.args.verbose
            )
            print(f"\nFinished reading file. Processed {self.packet_count} packets.")
            return

        # Open write file if specified
        if self.args.write_file:
            try:
                logger.info(f"Opening write file: {self.args.write_file}")
                with self._lock:
                    self.write_file_handle = open(self.args.write_file, "wb")
                print(f"Writing packets to {self.args.write_file}")
            except Exception as e:
                logger.error(f"Could not open write file '{self.args.write_file}': {e}")
                print(
                    f"Error: Could not open write file '{self.args.write_file}': {e}",
                    file=sys.stderr,
                )
                sys.exit(1)

        # Connect to device for live capture
        interface = self._connect_to_interface()
        # Initialize NodeBook once per MeshCap instance after connecting
        self.node_book = NodeBook(interface)

        def packet_handler(packet, interface):
            self._on_packet_received(
                packet, interface, self.args.no_resolve, self.args.verbose
            )

        pub.subscribe(packet_handler, "meshtastic.receive")

        # Handle test mode after subscription setup
        if self.args.test_mode:
            print("Test mode: Setup complete, exiting after subscription")
            with self._lock:
                if self.write_file_handle:
                    self.write_file_handle.close()
                    self.write_file_handle = None
            return

        count_msg = (
            f" (stopping after {self.target_count} packets)"
            if self.target_count
            else ""
        )
        print(f"Listening for packets{count_msg}... Press Ctrl+C to exit")
        try:
            while True:
                with self._lock:
                    should_exit = self.should_exit
                if should_exit:
                    break
                time.sleep(constants.SLEEP_INTERVAL)
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            interface.close()
            with self._lock:
                if self.write_file_handle:
                    self.write_file_handle.close()
                    self.write_file_handle = None

    def _connect_to_interface(self):
        """Connect to a Meshtastic device via serial or TCP interface.

        Returns:
            SerialInterface or TCPInterface: The connected interface object

        Raises:
            SystemExit: If connection fails, exits with status code 1
        """
        try:
            if self.args.host:
                # TCP connection
                logger.info(
                    f"Attempting TCP connection to {self.args.host}:{self.args.tcp_port}"
                )
                interface = meshtastic.tcp_interface.TCPInterface(
                    hostname=self.args.host, portNumber=self.args.tcp_port
                )
                logger.info(
                    f"TCP connection established to {self.args.host}:{self.args.tcp_port}"
                )
                print(
                    f"Successfully connected to device at {self.args.host}:{self.args.tcp_port}"
                )
            else:
                # Serial connection
                logger.info(f"Attempting serial connection to {self.args.port}")
                interface = meshtastic.serial_interface.SerialInterface(self.args.port)
                logger.info(f"Serial connection established to {self.args.port}")
                print(f"Successfully connected to device at {self.args.port}")
            return interface
        except ConnectionRefusedError as e:
            logger.error(
                f"TCP connection refused to {self.args.host}:{self.args.tcp_port}: {e}"
            )
            print(
                f"Error: TCP connection refused to {self.args.host}:{self.args.tcp_port}: {e}",
                file=sys.stderr,
            )
            sys.exit(1)
        except Exception as e:
            connection_type = (
                f"{self.args.host}:{self.args.tcp_port}"
                if self.args.host
                else self.args.port
            )
            logger.error(f"Connection to device at {connection_type} failed: {e}")
            print(
                f"Error: Connection to device at {connection_type} failed: {e}",
                file=sys.stderr,
            )
            sys.exit(1)

    def format_node_label(
        self, interface, node, label_mode="named-with-hex", no_resolve=False
    ):
        """Format a node identifier according to the specified label mode.

        Args:
            interface: The Meshtastic interface object for node lookups (can be None)
            node (int|str): The node identifier (int node number or str '!nodeid')
            label_mode (str): The label mode - "hex-only", "named-only", or "named-with-hex"
            no_resolve (bool): If True, skip node name resolution

        Returns:
            str: Formatted node label string
        """
        # Canonicalize with to_node_num
        node_num = to_node_num(node)
        user_id = to_user_id(node_num)

        # If no_resolve is True, return user_id directly
        if no_resolve:
            return user_id

        # Use cached NodeBook if available; fall back to a temporary one
        node_label = (
            self.node_book.get(node_num)
            if self.node_book is not None
            else NodeBook(interface).get(node_num)
        )

        # Handle different label modes
        if label_mode == "hex-only":
            return user_id
        elif label_mode == "named-only":
            best = node_label.best()
            return best if best != user_id else user_id
        elif label_mode == "named-with-hex":
            best = node_label.best()
            return f"{best} ({user_id})" if best != user_id else user_id
        else:
            raise ValueError(f"Unknown label_mode: {label_mode}")

    def _format_timestamp(self, packet: dict) -> str:
        """Format the timestamp from a packet.

        Args:
            packet: The packet dictionary containing rxTime

        Returns:
            str: Formatted timestamp string in YYYY-MM-DD HH:MM:SS format
        """
        timestamp = (
            datetime.fromtimestamp(packet.get("rxTime", 0), timezone.utc)
            .astimezone()
            .strftime("%Y-%m-%d %H:%M:%S")
        )
        return f"[{timestamp}]"

    def _format_signal_strength(self, packet: dict) -> str:
        """Format signal strength information from a packet.

        Args:
            packet: The packet dictionary containing signal strength data

        Returns:
            str: Formatted signal strength string (rssi/snr or '-')
        """
        rssi = packet.get("rxRssi", packet.get("rssi"))
        snr = packet.get("rxSnr")
        signal_parts = []
        if rssi is not None:
            signal_parts.append(f"{rssi}dBm")
        if snr is not None:
            signal_parts.append(f"{snr}dB")
        return "/".join(signal_parts) if signal_parts else "-"

    def _format_address_fields(self, packet: dict, interface, no_resolve: bool) -> str:
        """Format from/to address fields from a packet.

        Args:
            packet: The packet dictionary containing address information
            interface: The Meshtastic interface object for node lookups
            no_resolve: If True, skip node name resolution

        Returns:
            str: Formatted address string with from and to fields
        """

        def _label_or_unknown(tag):
            uid = packet.get(f"{tag}Id") or packet.get(tag)
            if not uid:
                return f"{tag}:unknown"
            return f"{tag}:{self.format_node_label(interface, uid, label_mode=self.args.label_mode, no_resolve=no_resolve)}"

        return f"{_label_or_unknown('from')} {_label_or_unknown('to')}"

    def _format_next_hop(self, packet: dict, interface, no_resolve: bool) -> str:
        """Format next hop information from a packet.

        Args:
            packet: The packet dictionary containing next hop data
            interface: The Meshtastic interface object for node lookups
            no_resolve: If True, skip node name resolution

        Returns:
            str: Formatted next hop string or empty string if no next hop
        """
        nh = packet.get("nextHop") or packet.get("next_hop")
        if isinstance(nh, int) and nh != 0:
            label = None
            if interface and getattr(interface, "nodes", None) and not no_resolve:
                matches = []
                for uid in interface.nodes.keys():
                    try:
                        if int(uid[-2:], 16) == (nh & 0xFF):
                            matches.append(uid)
                    except Exception:
                        continue
                if len(matches) == 1:
                    label = self.format_node_label(
                        interface,
                        matches[0],
                        label_mode=self.args.label_mode,
                        no_resolve=False,
                    )
            return f"NH:{label or f'0x{nh:02x}'}"
        return ""

    def _format_payload(self, packet: dict, verbose: bool) -> tuple[str, str]:
        """Format payload information from a packet.

        Args:
            packet: The packet dictionary containing payload data
            verbose: If True, include JSON payload details

        Returns:
            tuple[str, str]: A tuple of (packet_tag, json_payload)
        """
        decoded = packet.get("decoded") or {}
        packet_tag = ""
        if not decoded:
            enc = packet.get("encrypted", "")
            packet_tag = f"encrypted:len={len(enc)}" if enc is not None else ""

        extra = self.payload_formatter.format(packet)
        json_payload = str(decoded) if verbose else None

        return packet_tag, extra, json_payload

    def _format_packet(self, packet, interface, no_resolve, verbose=False):
        """Format a packet dictionary into a display string."""
        timestamp = self._format_timestamp(packet)
        channel_hash = f"Ch:{str(packet.get('channel', 0))}"
        signal = self._format_signal_strength(packet)

        # Hop + flags
        hop_info = self._format_hop_info(packet)
        flags_string = self._format_flags(packet)

        next_hop_info = self._format_next_hop(packet, interface, no_resolve)
        address_str = self._format_address_fields(packet, interface, no_resolve)

        packet_tag, extra, json_payload = self._format_payload(packet, verbose)

        # Assemble compactly, skipping empties to avoid double spaces
        parts = [
            timestamp,
            channel_hash,
            signal,
            hop_info,
            flags_string,
            next_hop_info,
            address_str,
            packet_tag,
            extra,
            json_payload,
        ]
        return " ".join(p for p in parts if p)


def main():
    parser = argparse.ArgumentParser(description="Meshtastic network dump tool")

    # Create mutually exclusive group for connection arguments
    connection_group = parser.add_mutually_exclusive_group()
    connection_group.add_argument(
        "-p",
        "--port",
        default=constants.DEFAULT_SERIAL_PORT,
        help=f"Serial device path (default: {constants.DEFAULT_SERIAL_PORT})",
    )
    connection_group.add_argument(
        "--host",
        help="TCP/IP hostname or IP address for network connection",
    )

    parser.add_argument(
        "--tcp-port",
        type=int,
        default=constants.DEFAULT_TCP_PORT,
        help=f"TCP port number for network connection (default: {constants.DEFAULT_TCP_PORT})",
    )
    parser.add_argument(
        "--test-mode",
        action="store_true",
        help="Run in test mode (exit immediately after setup)",
    )
    parser.add_argument(
        "-n",
        "--no-resolve",
        action="store_true",
        help="Disable node name resolution (use raw IDs)",
    )
    parser.add_argument(
        "-w",
        "--write-file",
        help="Write received packets to specified file in binary format",
    )
    parser.add_argument(
        "-r",
        "--read-file",
        help="Read packets from specified file instead of connecting to device",
    )
    parser.add_argument(
        "-c",
        "--count",
        type=int,
        help="Exit after receiving specified number of packets",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose output (show JSON details)",
    )
    parser.add_argument(
        "--label-mode",
        choices=["auto", "named-with-hex", "named-only", "hex-only"],
        default="named-with-hex",
        help="Node label display mode (default: named-with-hex, auto=named-with-hex)",
    )
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        default="WARNING",
        help="Set logging level (default: WARNING)",
    )
    parser.add_argument(
        "filter", nargs="*", help="Filter expression (e.g., 'src node A and port text')"
    )

    args = parser.parse_args()

    # Configure logging based on command line argument
    log_level = getattr(logging, args.log_level.upper())
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        stream=sys.stderr,
    )

    # Handle alias mapping: auto -> named-with-hex
    if args.label_mode == "auto":
        args.label_mode = "named-with-hex"

    capture = MeshCap(args)
    capture.run()


if __name__ == "__main__":
    main()
