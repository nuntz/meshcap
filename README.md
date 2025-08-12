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

## Command Line Options

- `--port/-p`: Serial device path (default: `/dev/ttyACM0`)
- `--test-mode`: Run in test mode (exit after setup)
- `--no-resolve/-n`: Disable node name resolution
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