import os
import time
import traceback
import zmq
from plico.utils.base_runner import BaseRunner
from plico.utils.logger import Logger
from plico.rpc.zmq_ports import ZmqPorts
from plico.rpc.sockets import Sockets
from plico.rpc.zmq_remote_procedure_call import ZmqRemoteProcedureCall
from plico_drive_server.drive.drive import Drive
from plico_drive_server.devices.meross_controller import MerossController
from plico_drive_server.utils.constants import Constants
from plico.utils.decorator import override


class DriveRunner(BaseRunner):
    """Drive runner class to handle drive server.
    
    This class handles the RPC requests to the drive server and
    forwards them to the appropriate drive device.
    """
    
    def __init__(self):
        """Create a runner for drive server."""
        BaseRunner.__init__(self)
        self._drive = None
        self._sockets = None
        self._poller = None
        self._drive_name = None
        self._drive_kwargs = {}
        
    @override
    def _createConfiguration(self):
        """Create the configuration object.
        
        Returns
        -------
        Configuration
            The configuration object
        """
        configuration = super()._createConfiguration()
        
        # Get drive configuration
        try:
            # Check if configuration is None before accessing getValue
            if configuration is None:
                print("Configuration is None, using default drive type 'meross'")
                self._drive_name = 'meross'
            else:
                self._drive_name = configuration.getValue('drive', 'type', 'meross')
            
            # Get Meross configuration if using Meross drive
            if self._drive_name.lower() == 'meross':
                self._drive_kwargs = {
                    'email': configuration.getValue('deviceMeross', 'email'),
                    'password': configuration.getValue('deviceMeross', 'password'),
                    'model': configuration.getValue('deviceMeross', 'model')
                }
        except KeyError as e:
            print(f"Missing required configuration: {str(e)}")
            raise
            
        return configuration
        
    @override
    def _createZmqBasedRPC(self):
        """Create the ZMQ-based RPC handler."""
        self._rpc = ZmqRemoteProcedureCall()
        
    @override
    def _registerHandlers(self):
        """Register the RPC handlers."""
        # Initialize drive device
        drive_device = self._create_drive_device()
        
        # Initialize sockets
        self._sockets = Sockets(self._ports, self._rpc)
        replySocket = self._sockets.serverRequest()
        statusSocket = self._sockets.serverStatus()
        
        # Create drive
        self._drive = Drive(
            name=self._argv[2],  # Use name from command line args
            ports=self._ports,
            drive_device=drive_device,
            replySocket=replySocket,
            statusSocket=statusSocket,
            rpc=self._rpc,
        )
        
        # Set up the socket poller
        self._poller = zmq.Poller()
        self._poller.register(replySocket, zmq.POLLIN)
        
        self._logger.notice(f"Runner {self._argv[2]} ready to handle requests")
        
    def _create_drive_device(self):
        """Create the appropriate drive device instance."""
        if self._drive_name.lower() == 'meross':
            self._logger.notice("Creating Meross drive")
            drive = MerossController(name=self._argv[2], **self._drive_kwargs)
        else:
            raise ValueError(f"Unsupported drive type: {self._drive_name}")
        
        return drive
        
    @override
    def _step(self):
        """Execute a single step of the control loop.
        
        Returns
        -------
        bool
            True if the operation was executed successfully
        """
        socks = dict(self._poller.poll(timeout=500))
        if self._sockets.serverRequest() in socks:
            try:
                self._sockets.rpc.handleRequest(self._sockets.serverRequest())
                return True
            except Exception as e:
                trace = traceback.format_exc()
                self._logger.error(
                    "Error handling request: %s\n%s" % (str(e), trace))
        return False
        
    @override
    def terminate(self):
        """Terminate the runner."""
        if self._isTerminated:
            return
            
        self._logger.notice("Terminating")
        self._isTerminated = True
        if self._drive:
            self._drive.terminate()
        if self._sockets:
            self._sockets.close()
        self._timingStatistics = None 