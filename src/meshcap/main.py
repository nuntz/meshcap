import argparse
import sys
import time
import pickle
from datetime import datetime, timezone
import meshtastic.serial_interface
from pubsub import pub
from .filter import parse_filter, evaluate_filter, FilterError


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
                    return  # Packet doesn't match filter, skip processing
            except FilterError as e:
                print(f"Warning: Filter evaluation error: {e}", file=sys.stderr)
                return

        # Write packet to file if writer is enabled
        if self.write_file_handle:
            pickle.dump(packet, self.write_file_handle)

        # Format and print the packet
        formatted = self._format_packet(packet, interface, no_resolve, verbose)
        print(formatted)

        # Increment packet counter (only for matching packets)
        self.packet_count += 1

        # Check if we've reached the target count
        if self.target_count and self.packet_count >= self.target_count:
            print(f"\nProcessed {self.packet_count} matching packets. Exiting...")
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
        try:
            with open(filename, "rb") as f:
                while True:
                    try:
                        packet = pickle.load(f)
                        self._on_packet_received(packet, None, no_resolve, verbose)
                    except EOFError:
                        break
        except FileNotFoundError:
            print(f"Error: File '{filename}' not found", file=sys.stderr)
            sys.exit(1)
        except Exception as e:
            print(f"Error reading from file '{filename}': {e}", file=sys.stderr)
            sys.exit(1)

    def run(self):
        """Run the main application logic."""
        # Parse filter expression if provided
        if self.args.filter:
            try:
                self.filter_rpn = parse_filter(self.args.filter)
                print(f"Using filter: {' '.join(self.args.filter)}")
            except FilterError as e:
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
                self.write_file_handle = open(self.args.write_file, "wb")
                print(f"Writing packets to {self.args.write_file}")
            except Exception as e:
                print(
                    f"Error: Could not open write file '{self.args.write_file}': {e}",
                    file=sys.stderr,
                )
                sys.exit(1)

        # Connect to device for live capture
        interface = self._connect_to_device(self.args.port)

        def packet_handler(packet, interface):
            self._on_packet_received(
                packet, interface, self.args.no_resolve, self.args.verbose
            )

        pub.subscribe(packet_handler, "meshtastic.receive")

        # Handle test mode after subscription setup
        if self.args.test_mode:
            print("Test mode: Setup complete, exiting after subscription")
            if self.write_file_handle:
                self.write_file_handle.close()
            return

        count_msg = (
            f" (stopping after {self.target_count} packets)"
            if self.target_count
            else ""
        )
        print(f"Listening for packets{count_msg}... Press Ctrl+C to exit")
        try:
            while not self.should_exit:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nExiting...")
        finally:
            interface.close()
            if self.write_file_handle:
                self.write_file_handle.close()

    def _connect_to_device(self, port):
        """Connect to a Meshtastic device via serial interface.

        Args:
            port (str): The serial port path to connect to

        Returns:
            SerialInterface: The connected interface object

        Raises:
            SystemExit: If connection fails, exits with status code 1
        """
        try:
            interface = meshtastic.serial_interface.SerialInterface(port)
            print(f"Successfully connected to device at {port}")
            return interface
        except Exception as e:
            print(f"Error: Connection to device failed: {e}", file=sys.stderr)
            sys.exit(1)

    def _resolve_node_info(self, interface, node_identifier, identifier_type):
        """Resolve a node identifier to a formatted display string with label.

        Args:
            interface: The Meshtastic interface object for node lookups (can be None)
            node_identifier: The node identifier (int node number or str '!nodeid')
            identifier_type (str): The type of identifier ('from', 'to', 'source', 'dest')

        Returns:
            dict: Dictionary with 'label' and 'value' keys
        """
        # Convert integer node identifier to string format
        if isinstance(node_identifier, int):
            node_id_str = f"!{node_identifier:08x}"
        else:
            node_id_str = str(node_identifier)

        # Check if resolution is disabled or interface unavailable
        if self.args.no_resolve or interface is None:
            return {"label": identifier_type, "value": node_id_str}

        # Try to resolve using interface.nodes
        if interface and hasattr(interface, "nodes") and node_id_str in interface.nodes:
            node = interface.nodes[node_id_str]
            if "user" in node and "longName" in node["user"]:
                resolved_name = node["user"]["longName"]
                return {
                    "label": identifier_type,
                    "value": f"{resolved_name} ({node_id_str})",
                }

        return {"label": identifier_type, "value": node_id_str}

    def _node_ids_differ(self, id1, id2):
        """Check if two node identifiers represent different nodes.

        Args:
            id1: First node identifier (str or int)
            id2: Second node identifier (str or int)

        Returns:
            bool: True if the IDs represent different nodes
        """
        # Convert both to consistent format for comparison
        if isinstance(id1, int):
            id1_str = f"!{id1:08x}"
        else:
            id1_str = str(id1)

        if isinstance(id2, int):
            id2_str = f"!{id2:08x}"
        else:
            id2_str = str(id2)

        return id1_str != id2_str

    def _format_packet(self, packet, interface, no_resolve, verbose=False):
        """Format a packet dictionary into a display string.

        Args:
            packet (dict): The packet dictionary from Meshtastic
            interface: The Meshtastic interface object for node lookups
            no_resolve (bool): If True, skip node name resolution
            verbose (bool): If True, show JSON details for unknown packet types

        Returns:
            str: Formatted packet string
        """
        # Store resolution setting for use by helper methods
        self.args.no_resolve = no_resolve
        timestamp = datetime.fromtimestamp(
            packet.get("rxTime", 0), timezone.utc
        ).strftime("%Y-%m-%d %H:%M:%S")

        channel_hash = str(packet.get("channel", 0))

        rssi = packet.get("rxRssi", 0)
        snr = packet.get("rxSnr", 0)
        signal = f"{rssi}dBm/{snr}dB"
        
        hop_limit = packet.get("hopLimit", 0)
        hop_info = f" Hop:{hop_limit}"

        # Build clean address string with proper labels
        address_parts = []

        # Primary addressing - immediate hop (most common case)
        from_id = packet.get("fromId")
        to_id = packet.get("toId")

        if from_id:
            address_parts.append(self._resolve_node_info(interface, from_id, "from"))

        if to_id:
            address_parts.append(self._resolve_node_info(interface, to_id, "to"))

        # Secondary addressing - numeric IDs (for backwards compatibility)
        from_num = packet.get("from")
        to_num = packet.get("to")

        # Only show numeric IDs if they differ from string IDs or if string IDs are missing
        if from_num and (not from_id or self._node_ids_differ(from_id, from_num)):
            address_parts.append(
                self._resolve_node_info(interface, from_num, "hop_from")
            )

        if to_num and (not to_id or self._node_ids_differ(to_id, to_num)):
            address_parts.append(self._resolve_node_info(interface, to_num, "hop_to"))

        # End-to-end routing information
        decoded = packet.get("decoded", {})
        if decoded:
            source_num = decoded.get("source")
            dest_num = decoded.get("dest")

            if source_num and (
                not from_id or self._node_ids_differ(from_id, source_num)
            ):
                address_parts.append(
                    self._resolve_node_info(interface, source_num, "source")
                )

            if dest_num and (not to_id or self._node_ids_differ(to_id, dest_num)):
                address_parts.append(
                    self._resolve_node_info(interface, dest_num, "dest")
                )

        # Build final address string
        if address_parts:
            address_str = " ".join(
                f"{part['label']}:{part['value']}" for part in address_parts
            )
        else:
            address_str = "from:unknown to:unknown"

        # Format packet payload
        if decoded and "portnum" in decoded:
            portnum = decoded["portnum"]

            if portnum == "TEXT_MESSAGE_APP":
                packet_type = "Text"
                payload = decoded.get("text", "")
            elif portnum == "POSITION_APP":
                packet_type = "Position"
                position = decoded.get("position", {})
                lat = position.get("latitude", 0)
                lon = position.get("longitude", 0)
                payload = f"lat={lat}, lon={lon}"
            else:
                packet_type = portnum
                payload = str(decoded) if verbose else f"[{portnum}]"
        else:
            packet_type = "Encrypted"
            payload = f"length={len(packet.get('encrypted', ''))}"

        return f"[{timestamp}] Ch:{channel_hash} {signal}{hop_info} {address_str} {packet_type}: {payload}"


def main():
    parser = argparse.ArgumentParser(description="Meshtastic network dump tool")
    parser.add_argument(
        "-p",
        "--port",
        default="/dev/ttyACM0",
        help="Serial device path (default: /dev/ttyACM0)",
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
        "filter", nargs="*", help="Filter expression (e.g., 'src node A and port text')"
    )

    args = parser.parse_args()
    capture = MeshCap(args)
    capture.run()


if __name__ == "__main__":
    main()
