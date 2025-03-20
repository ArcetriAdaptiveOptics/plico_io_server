import os
import time
from plico.utils.base_runner import BaseRunner
from plico.utils.logger import Logger
from plico.rpc.zmq_ports import ZmqPorts
from plico.rpc.zmq_remote_procedure_call import ZmqRemoteProcedureCall
from plico_io_server.controller.controller import Controller
from plico_io_server.devices.meross_controller import MerossController
from plico_io_server.utils.constants import Constants
from plico.utils.decorator import override
from plico.utils.control_loop import FaultTolerantControlLoop


class ControllerRunner(BaseRunner):
    """Controller runner class to handle controller server.
    
    This class handles the RPC requests to the controller server and
    forwards them to the appropriate controller device.
    """
    
    RUNNING_MESSAGE = "Controller server is running."
    
    def __init__(self):
        """Create a runner for controller server."""
        BaseRunner.__init__(self)
        self._controller = None
        self._controller_device = None
        self._logger = Logger.of(self.__class__.__name__)
        
    def _createControllerDevice(self):
        """Create the appropriate controller device based on configuration."""
        # Get the controller device section from the configuration
        controllerDeviceSection = self.configuration.getValue(
            self.getConfigurationSection(), 'controller')
        
        # Get the device model
        controllerModel = self.configuration.deviceModel(
            controllerDeviceSection)
            
        if controllerModel == 'meross':
            self._createMerossController(controllerDeviceSection)
        else:
            raise KeyError('Unsupported controller model %s' % controllerModel)
            
    def _createMerossController(self, controllerDeviceSection):
        """Create a Meross controller device instance."""
        # Get the device name from the configuration
        name = self.configuration.deviceName(controllerDeviceSection)
        
        # Get Meross-specific configuration
        email = self.configuration.getValue(controllerDeviceSection, 'email')
        password = self.configuration.getValue(controllerDeviceSection, 'password')
        device_type = self.configuration.getValue(controllerDeviceSection, 'device_type')
        
        self._controller_device = MerossController(
            name=name,
            email=email,
            password=password,
            model=device_type)
            
    def _replyPort(self):
        """Get the reply port from configuration."""
        return self.configuration.replyPort(self.getConfigurationSection())
        
    def _publisherPort(self):
        """Get the publisher port from configuration."""
        return self.configuration.publisherPort(self.getConfigurationSection())
        
    def _statusPort(self):
        """Get the status port from configuration."""
        return self.configuration.statusPort(self.getConfigurationSection())
        
    def _setUp(self):
        """Set up the controller server."""
        self._logger = Logger.of("Controller runner")
        
        self._zmqPorts = ZmqPorts.fromConfiguration(
            self.configuration, self.getConfigurationSection())
        self._replySocket = self.rpc().replySocket(
            self._zmqPorts.SERVER_REPLY_PORT)
        self._publishSocket = self.rpc().publisherSocket(
            self._zmqPorts.SERVER_PUBLISHER_PORT, hwm=100)
        self._statusSocket = self.rpc().publisherSocket(
            self._zmqPorts.SERVER_STATUS_PORT, hwm=1)
            
        self._createControllerDevice()
        
        self._controller = Controller(
            self.name,
            self._zmqPorts,
            self._controller_device,
            self._replySocket,
            self._statusSocket,
            self.rpc())
            
        self._logger.notice(f"Runner {self.name} ready to handle requests")
        
    def _runLoop(self):
        """Run the control loop."""
        self._logRunning()
        
        FaultTolerantControlLoop(
            self._controller,
            Logger.of("Controller control loop"),
            time,
            0.02).start()
        self._logger.notice("Terminated")
        
    @override
    def run(self):
        """Run the controller server.
        
        Returns
        -------
        int
            Exit code (0 for success)
        """
        self._setUp()
        self._runLoop()
        return os.EX_OK
        
    @override
    def terminate(self, signal, frame):
        """Terminate the runner."""
        if self._controller:
            self._controller.terminate() 