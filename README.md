# meshcap

A Python command-line tool for working with Meshtastic networks, providing packet capture, filtering, and analysis capabilities.

## Installation

This project uses `uv` as the package manager. To install dependencies:

```bash
uv sync
```

## Usage

### Basic Usage

```bash
# Run with default port (/dev/ttyACM0)
uv run meshcap

# Run with custom port
uv run meshcap --port /dev/ttyUSB0
uv run meshcap -p /dev/ttyUSB0

# Run with verbose output (shows JSON details for unknown packet types)
uv run meshcap --verbose
uv run meshcap -v
```

### Packet Filtering

meshcap supports advanced packet filtering using logical expressions:

```bash
# Filter text messages only
uv run meshcap port text

# Messages from specific node and text port
uv run meshcap src node A and port text

# Complex filtering with parentheses
uv run meshcap '(' src node A or dst node A ')' and port position
```

### File Operations

```bash
# Write packets to file
uv run meshcap --write-file packets.bin

# Read from file with filtering
uv run meshcap -r packets.bin encrypted and hop_limit '>' 5

# Limit packet count
uv run meshcap -c 10 priority HIGH or want_ack
```

## Output Format

meshcap displays captured packets in a structured format showing timestamp, channel, signal strength, hop limit, addressing information, packet type, and payload:

```
[timestamp] Ch:hash signal Hop:X address_fields packet_type: payload
```

### Node Identity & Labels

meshcap uses a flexible node identity model:

- **Canonical NodeNum**: Each Meshtastic node has a canonical node number (e.g., `3735928559`)
- **User ID view**: Node IDs can be displayed as hex strings (e.g., `!deadbeef`)
- **Labels optional**: User names/labels are optional and displayed as `Name(!deadbeef)` when available

### Examples

**Node identity with new display form:**
```
[2023-10-19 16:02:15] Ch:3 -85dBm/10.0dB Hop:0 from:TestNode (!deadbeef) to:Relay (!cafebabe) Text: New identity format
```

### Field Types

- **Hop:X**: Remaining hop limit for the packet (how many more hops it can make)
- **from/to**: End-to-end message routing (ultimate origin/destination)

### Address Display Formats

- **Node numbers**: Raw integers (e.g., `123456789`) - preferred for readability
- **Node IDs**: Hex format (e.g., `!075bcd15`) - fallback when node numbers unavailable
- **Resolved names**: `Name (identifier)` format - shows user name with node number/ID

The tool only shows address fields that are present and differ from each other, keeping output clean while providing comprehensive routing information when available. The hop limit is always displayed when available, defaulting to 0 when not present in the packet.

## Command Line Options

- `--port/-p`: Serial device path (default: `/dev/ttyACM0`)
- `--test-mode`: Run in test mode (exit after setup)
- `--no-resolve/-n`: Disable node name resolution (show raw node numbers/IDs without names)
- `--write-file/-w`: Write packets to binary file
- `--read-file/-r`: Read packets from file
- `--count/-c`: Exit after N packets
- `--verbose/-v`: Enable verbose output (show JSON details for unknown packet types)
- `filter`: Filter expression

## Filter Syntax

### Primitives

- `node <value>`: Match packets from or to node
- `src node <value>`: Match source node
- `dst node <value>`: Match destination node
- `user <name>`: Match packets from or to a user by long or short name
- `src user <name>`: Match source user
- `dst user <name>`: Match destination user
- `port <value>`: Match port (supports: text, position, nodeinfo, routing, admin, telemetry)
- `hop_limit <op> <value>`: Match hop limit (`<`, `>`, `=`)
- `priority <value>`: Match priority level
- `want_ack`: Match packets requiring acknowledgment
- `encrypted`/`is encrypted`: Match encrypted packets
- `plaintext`/`is plaintext`: Match plaintext packets

### Operators

- `and`: Logical AND (higher precedence)
- `or`: Logical OR (lower precedence)
- `not`: Logical NOT (highest precedence)
- `( )`: Parentheses for grouping

### Examples

```bash
# Text messages from specific node
uv run meshcap src node !12345678 and port text

# Messages from the user named "Alice"
uv run meshcap src user Alice

# High priority or ack-required packets
uv run meshcap priority HIGH or want_ack

# Complex expression
uv run meshcap '(' src node A or dst node A ')' and '(' port text or port position ')'

# Encrypted high hop-limit packets
uv run meshcap encrypted and hop_limit '>' 5

# Filtering with mixed node ID forms (hex and decimal)
uv run meshcap node src == !deadbeef
uv run meshcap node src == 3735928559

# Show verbose output for unknown packet types
uv run meshcap --verbose port admin
```

## Development

### Testing

```bash
# Run all tests
uv run pytest

# Run specific test file
uv run pytest tests/test_filtering.py

# Verbose output
uv run pytest -v
```

### Building

```bash
# Build package
uv build
```

## Project Structure

- `src/meshcap/main.py`: Main CLI application
- `src/meshcap/filter.py`: Packet filtering engine
- `tests/`: Test suite
- `pyproject.toml`: Project configuration

## Dependencies

- `meshtastic`: Core Meshtastic library
- `pytest`: Testing framework
