import argparse
import sys
import time
import pickle
from datetime import datetime, timezone
from typing import Dict, Union, Optional, Any
import meshtastic.serial_interface
from pubsub import pub
from .filter import parse_filter, evaluate_filter, FilterError
from .identifiers import to_node_num, to_user_id, NodeBook


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

    def _resolve_node_info(
        self,
        interface: Optional[Any],
        node_identifier: Union[int, str],
        identifier_type: str,
    ) -> Dict[str, Union[str, int]]:
        """Resolve a node identifier to a formatted display string with label.

        Args:
            interface: The Meshtastic interface object for node lookups (can be None)
            node_identifier: The node identifier (int node number or str '!nodeid')
            identifier_type: The type of identifier ('from', 'to', 'source', 'dest')

        Returns:
            Dictionary with 'label', 'value' and optional 'node_number' keys
        """
        from .identifiers import to_node_num
        
        # Canonicalize the node identifier to get node_number
        node_number = to_node_num(node_identifier)
        
        # Use format_node_label to get the formatted value
        formatted_value = self.format_node_label(
            interface, node_identifier, label_mode=getattr(self.args, 'label_mode', 'named-with-hex'), no_resolve=getattr(self.args, 'no_resolve', False)
        )
        
        # Build return dict with label and value
        result = {
            "label": identifier_type,
            "value": formatted_value,
        }
        
        # Add node_number if it's available and different from the original identifier
        if isinstance(node_identifier, int):
            result["node_number"] = node_number
        
        return result

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

    def format_node_label(self, interface, node, label_mode="named-with-hex", no_resolve=False):
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
        
        # Use NodeBook to get node information
        node_book = NodeBook(interface)
        node_label = node_book.get(node_num)
        
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

        # Optional next-hop display (only when set and non-zero)
        next_hop_info = ""
        next_hop_candidate = packet.get("nextHop") or packet.get("next_hop")
        if next_hop_candidate is not None:
            try:
                # Zero means "unset" for next hop
                if to_node_num(next_hop_candidate) != 0:
                    nh_label = self.format_node_label(
                        interface,
                        next_hop_candidate,
                        label_mode=self.args.label_mode,
                        no_resolve=no_resolve,
                    )
                    next_hop_info = f" NH:{nh_label}"
            except Exception:
                # Be conservative: if parsing fails, omit next-hop
                pass

        # Extract canonical from/to candidates
        from_candidate = packet.get("fromId") or packet.get("from")
        to_candidate = packet.get("toId") or packet.get("to")

        # Build clean address string with canonical addressing
        address_parts = []
        
        if from_candidate:
            from_label = self.format_node_label(interface, from_candidate, label_mode=self.args.label_mode, no_resolve=no_resolve)
            address_parts.append(f"from:{from_label}")
        else:
            address_parts.append("from:unknown")
            
        if to_candidate:
            to_label = self.format_node_label(interface, to_candidate, label_mode=self.args.label_mode, no_resolve=no_resolve)
            address_parts.append(f"to:{to_label}")
        else:
            address_parts.append("to:unknown")

        address_str = " ".join(address_parts)

        # Format packet payload
        decoded = packet.get("decoded", {})
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

        return f"[{timestamp}] Ch:{channel_hash} {signal}{hop_info}{next_hop_info} {address_str} {packet_type}: {payload}"


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
        "--label-mode",
        choices=["auto", "named-with-hex", "named-only", "hex-only"],
        default="named-with-hex",
        help="Node label display mode (default: named-with-hex, auto=named-with-hex)",
    )
    parser.add_argument(
        "filter", nargs="*", help="Filter expression (e.g., 'src node A and port text')"
    )

    args = parser.parse_args()
    
    # Handle alias mapping: auto -> named-with-hex
    if args.label_mode == "auto":
        args.label_mode = "named-with-hex"
    
    capture = MeshCap(args)
    capture.run()


if __name__ == "__main__":
    main()
