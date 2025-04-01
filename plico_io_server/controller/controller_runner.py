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
    # Default iteration interval = 36 seconds (100 times per hour)
    DEFAULT_ITERATION_INTERVAL_SEC = 36.0
    
    def __init__(self):
        """Create a runner for controller server."""
        BaseRunner.__init__(self)
        self._controller = None
        self._controller_device = None
        self._logger = Logger.of(self.__class__.__name__)
        self._iteration_interval_sec = self.DEFAULT_ITERATION_INTERVAL_SEC
        
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
        
    def _getIterationInterval(self):
        """Get the iteration interval from configuration or use default."""
        try:
            # Try to get custom interval from configuration, with a minimum allowed value
            interval_sec = float(self.configuration.getValue(
                self.getConfigurationSection(), 'iteration_interval_sec', 
                self.DEFAULT_ITERATION_INTERVAL_SEC))
            
            # Enforce minimum threshold to prevent excessive load
            MIN_INTERVAL_SEC = 1.0  # Minimum 1 second between iterations
            if interval_sec < MIN_INTERVAL_SEC:
                self._logger.warning(
                    f"Configured iteration interval {interval_sec}s is below minimum threshold. "
                    f"Using minimum value of {MIN_INTERVAL_SEC}s")
                interval_sec = MIN_INTERVAL_SEC
                
            return interval_sec
        except (ValueError, KeyError) as e:
            self._logger.notice(
                f"Using default iteration interval of {self.DEFAULT_ITERATION_INTERVAL_SEC}s "
                f"(100 iterations per hour)")
            return self.DEFAULT_ITERATION_INTERVAL_SEC
        
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
        
        # Get the iteration interval from configuration
        self._iteration_interval_sec = self._getIterationInterval()
        self._logger.notice(
            f"Controller will run at maximum {3600/self._iteration_interval_sec:.1f} times per hour "
            f"(every {self._iteration_interval_sec:.1f}s)")
        
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
            self._iteration_interval_sec).start()
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