# PLICO IO Server

A Python package for running a PLICO server that controls IO devices. This package provides a server implementation that can manage various IO devices (like Meross smart plugs) and expose them through the PLICO framework.

## Installation

```bash
pip install plico_io_server
```

## Configuration

The server uses a configuration file to store device settings. The default configuration file is located at:
- Windows: `%LOCALAPPDATA%\INAF Arcetri Adaptive Optics\inaf.arcetri.ao.plico_io_server\plico_io_server.conf`
- Linux/Mac: `~/.local/share/inaf.arcetri.ao.plico_io_server/plico_io_server.conf`

Example configuration file:
```ini
[server]
host = localhost
port = 5010
status_port = 5012

[controller1]
type = meross
name = Meross Smart Plug
model = MSS425E
device_id = 2008205514112290825648e1e92cbcf7
```

### Adding New Devices

To add a new device to the configuration:

1. Add a new section for your device:
```ini
[controller2]
type = meross
name = Another Smart Plug
model = MSS425E
device_id = your_device_id_here
```

2. The `type` field determines which controller class to use. Currently supported types:
   - `meross`: For Meross smart plugs

3. Other fields depend on the device type:
   - For Meross devices:
     - `name`: Display name for the device
     - `model`: Device model (e.g., MSS425E)
     - `device_id`: Unique identifier for the device

## Running the Server

### Command Line

```bash
# Start the server with default configuration
plico_io_server

# Start with custom configuration file
plico_io_server --config /path/to/config.conf

# Start with specific host and port
plico_io_server --host localhost --port 5010
```

### Python API

```python
from plico_io_server.server.controller_server import ControllerServer
from plico_io_server.utils.builder import ControllerServerBuilder

# Using the builder pattern (recommended)
builder = ControllerServerBuilder()
server = builder.host('localhost').port(5010).build()

# Or from configuration
from plico.utils.configuration import Configuration
config = Configuration()
config.load('path/to/config.conf')
server = builder.from_configuration(config).build()

# Start the server
server.start()

# ... do your work ...

# Stop the server
server.stop()
```

## Testing

The package includes several test scripts in the `examples` directory:
- `meross_server_test.py`: Tests the Meross server functionality
- `meross_client_test.py`: Tests client-server communication
- `meross_client_pulse.py`: Tests pulse pattern generation

## Development

To set up a development environment:

1. Clone the repository
2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install development dependencies:
```bash
pip install -e ".[dev]"
```

4. Run tests:
```bash
pytest
``` 