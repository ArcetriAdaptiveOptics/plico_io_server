import time
import json
from plico.utils.logger import Logger
from plico.rpc.zmq_ports import ZmqPorts
from plico.rpc.sockets import Sockets
from plico.rpc.zmq_remote_procedure_call import ZmqRemoteProcedureCall
from plico_drive_server.utils.constants import Constants


class Drive:
    """Drive class to handle drive device operations.
    
    This class handles the RPC requests to the drive device and
    forwards them to the appropriate device methods.
    """
    
    def __init__(self, name, ports, drive_device, replySocket, statusSocket, rpc):
        """Create a drive instance.
        
        Parameters
        ----------
        name : str
            Name of the drive instance
        ports : ZmqPorts
            An instance of ZmqPorts with the configuration
        drive_device : object
            The drive device instance to handle operations
        replySocket : zmq.Socket
            Socket for sending replies
        statusSocket : zmq.Socket
            Socket for sending status updates
        rpc : ZmqRemoteProcedureCall
            RPC handler instance
        """
        self._name = name
        self._ports = ports
        self._drive_device = drive_device
        self._replySocket = replySocket
        self._statusSocket = statusSocket
        self._rpc = rpc
        self._logger = Logger.of(name)
        
        # Register RPC methods
        self._registerRpcMethods()
        
    def _registerRpcMethods(self):
        """Register RPC methods with the RPC handler."""
        self._rpc.registerRpcMethod(self.getStatus)
        self._rpc.registerRpcMethod(self.getSnapshot)
        self._rpc.registerRpcMethod(self.turnOn)
        self._rpc.registerRpcMethod(self.turnOff)
        
    def getStatus(self):
        """Get the current status of the drive device.
        
        Returns
        -------
        dict
            Current status of the drive device
        """
        return self._drive_device.getStatus()
        
    def getSnapshot(self):
        """Get a snapshot of the drive device state.
        
        Returns
        -------
        dict
            Snapshot of the drive device state
        """
        return self._drive_device.getSnapshot()
        
    def turnOn(self):
        """Turn on the drive device.
        
        Returns
        -------
        bool
            True if the operation was successful
        """
        return self._drive_device.turnOn()
        
    def turnOff(self):
        """Turn off the drive device.
        
        Returns
        -------
        bool
            True if the operation was successful
        """
        return self._drive_device.turnOff()
        
    def terminate(self):
        """Terminate the drive instance."""
        self._logger.notice("Terminating")
        self._drive_device.terminate() 