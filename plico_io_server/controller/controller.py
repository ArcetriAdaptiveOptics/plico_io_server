import time
import json
from plico.utils.logger import Logger
from plico.rpc.zmq_ports import ZmqPorts
from plico.rpc.sockets import Sockets
from plico.rpc.zmq_remote_procedure_call import ZmqRemoteProcedureCall
from plico_io_server.utils.constants import Constants
from plico.utils.decorator import override
from plico.utils.stepable import Stepable


class Controller(Stepable):
    """Controller class to handle controller device operations.
    
    This class handles the RPC requests to the controller device and
    forwards them to the appropriate device methods.
    """
    
    def __init__(self, name, ports, controller_device, replySocket, statusSocket, rpc):
        """Create a controller instance.
        
        Parameters
        ----------
        name : str
            Name of the controller instance
        ports : ZmqPorts
            An instance of ZmqPorts with the configuration
        controller_device : object
            The controller device instance to handle operations
        replySocket : zmq.Socket
            Socket for sending replies
        statusSocket : zmq.Socket
            Socket for sending status updates
        rpc : ZmqRemoteProcedureCall
            RPC handler instance
        """
        self._name = name
        self._ports = ports
        self._controller_device = controller_device
        self._replySocket = replySocket
        self._statusSocket = statusSocket
        self._rpc = rpc
        self._logger = Logger.of(name)
        self._isTerminated = False
        self._stepCounter = 0
        self._timekeep = time.time()
        
    @override
    def step(self):
        """Process RPC requests and publish status updates."""
        self._rpc.handleRequest(self, self._replySocket, multi=True)
        self._publishStatus()
        if time.time() - self._timekeep >= 1.0:
            self._logger.notice('Stepping at %5.2f Hz' % (self._stepCounter / (time.time() - self._timekeep)))
            self._timekeep = time.time()
            self._stepCounter = 0
        self._stepCounter += 1
        
    def _publishStatus(self):
        """Publish the current status of the controller device."""
        self._rpc.publishPickable(self._statusSocket, self.getStatus())
        
    def getStatus(self):
        """Get the current status of the controller device.
        
        Returns
        -------
        dict
            Current status of the controller device
        """
        return self._controller_device.getStatus()
        
    def getSnapshot(self):
        """Get a snapshot of the controller device state.
        
        Returns
        -------
        dict
            Snapshot of the controller device state
        """
        return self._controller_device.getSnapshot()
        
    def turnOn(self):
        """Turn on the controller device.
        
        Returns
        -------
        bool
            True if the operation was successful
        """
        return self._controller_device.turnOn()
        
    def turnOff(self):
        """Turn off the controller device.
        
        Returns
        -------
        bool
            True if the operation was successful
        """
        return self._controller_device.turnOff()
        
    def terminate(self):
        """Terminate the controller instance."""
        self._logger.notice("Terminating")
        self._controller_device.terminate()
        self._isTerminated = True
        
    @override
    def isTerminated(self):
        """Check if the controller has been terminated.
        
        Returns
        -------
        bool
            True if the controller has been terminated
        """
        return self._isTerminated 