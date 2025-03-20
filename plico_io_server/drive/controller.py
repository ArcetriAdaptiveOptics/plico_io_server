import time
import threading
from plico.utils.logger import Logger
from plico.utils.decorator import override
from plico_controller_server.controller_types.controller_status import ControllerStatus


class Controller:
    """Controller class to handle device operations."""
    
    def __init__(self, name, ports, controller_device, replySocket, statusSocket, rpc):
        """Create a controller.
        
        Parameters
        ----------
        name : str
            Name of the controller
        ports : ZmqPorts
            Port configuration
        controller_device : AbstractController
            The controller device instance
        replySocket : zmq.Socket
            Socket for RPC replies
        statusSocket : zmq.Socket
            Socket for status updates
        rpc : ZmqRemoteProcedureCall
            RPC handler
        """
        self._name = name
        self._ports = ports
        self._device = controller_device
        self._replySocket = replySocket
        self._statusSocket = statusSocket
        self._rpc = rpc
        self._logger = Logger.of(name)
        self._isTerminated = False
        self._statusThread = None
        
        # Start status update thread
        self._startStatusThread()
    
    def _startStatusThread(self):
        """Start the status update thread."""
        self._statusThread = threading.Thread(target=self._statusLoop, daemon=True)
        self._statusThread.start()
    
    def _statusLoop(self):
        """Status update loop."""
        while not self._isTerminated:
            try:
                self._publishStatus()
                time.sleep(1)
            except Exception as e:
                self._logger.error(f"Error publishing status: {str(e)}")
                time.sleep(1)
    
    def _publishStatus(self):
        """Publish current status."""
        try:
            devices = self._device.list_devices()
            # Convert devices to a serializable format
            serializable_devices = {}
            for device_id, device in devices.items():
                if hasattr(device, 'name'):
                    serializable_devices[device_id] = {
                        'name': device.name,
                        'status': self._device.get_status(device_id)
                    }
                else:
                    serializable_devices[device_id] = str(device)
            
            status = ControllerStatus(self._name, serializable_devices)
            self._statusSocket.send_json(status.getSnapshot(self._name))
        except Exception as e:
            self._logger.error(f"Error publishing status: {str(e)}")
    
    @override
    def name(self):
        """Get the controller name.
        
        Returns
        -------
        str
            The controller name
        """
        return self._name
    
    def turn_on(self, device_id=None, channel=0):
        """Turn on a device.
        
        Parameters
        ----------
        device_id : str, optional
            ID of the device to turn on
        channel : int, optional
            Channel number (default: 0)
            
        Returns
        -------
        bool
            True if successful
        """
        return self._device.turn_on(device_id, channel)
    
    def turn_off(self, device_id=None, channel=0):
        """Turn off a device.
        
        Parameters
        ----------
        device_id : str, optional
            ID of the device to turn off
        channel : int, optional
            Channel number (default: 0)
            
        Returns
        -------
        bool
            True if successful
        """
        return self._device.turn_off(device_id, channel)
    
    def get_status(self, device_id=None, channel=0):
        """Get device status.
        
        Parameters
        ----------
        device_id : str, optional
            ID of the device to check
        channel : int, optional
            Channel number (default: 0)
            
        Returns
        -------
        bool
            True if device is on
        """
        return self._device.get_status(device_id, channel)
    
    def list_devices(self):
        """List available devices.
        
        Returns
        -------
        dict
            Dictionary of available devices
        """
        return self._device.list_devices()
    
    def terminate(self):
        """Terminate the controller."""
        self._isTerminated = True
        if self._statusThread:
            self._statusThread.join(timeout=1)
        self._device.deinitialize() 