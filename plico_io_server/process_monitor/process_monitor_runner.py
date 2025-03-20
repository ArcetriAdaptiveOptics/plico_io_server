import os
import time
import traceback
from plico.utils.base_runner import BaseRunner
from plico.utils.logger import Logger
from plico.rpc.zmq_ports import ZmqPorts
from plico.rpc.sockets import Sockets
from plico.rpc.zmq_remote_procedure_call import ZmqRemoteProcedureCall
from plico.utils.serverinfoable import ServerInfoable
from plico_controller_server.utils.constants import Constants
from plico.utils.process_monitor import ProcessMonitor


class ProcessMonitorRunner(BaseRunner):
    """Monitor all plico-controller processes.
    
    This class provides a process monitor for plico-controller processes,
    allowing to check the status of running server processes.
    """
    
    def __init__(self, name, ports):
        """Create a process monitor runner.
        
        Parameters
        ----------
        name : str
            Name of the process monitor
        ports : ZmqPorts
            Ports configuration
        """
        BaseRunner.__init__(self)
        
        self._name = name
        self._ports = ports
        self._logger = Logger.of(name)
        
        # Initialize RPC
        rpcHandler = ZmqRemoteProcedureCall()
        
        # Initialize sockets
        self._sockets = Sockets(name, ports)
        self._replySocket = self._sockets.serverReply()
        
        # Create process monitor
        processes = {}
        processes[Constants.SERVER_PROCESS_NAME] = {
            'pingPort': ports.get(Constants.SERVER_PROCESS_NAME, 'pingPort'),
        }
        self._processMonitor = ProcessMonitor(processes)
        
        # Register RPC methods
        methods = {}
        methods['ping'] = self._ping
        methods['get_alive_process_list'] = self._processMonitor.getAliveProcessList
        methods['get_dead_process_list'] = self._processMonitor.getDeadProcessList
        methods['get_processes_status'] = self._processMonitor.getProcessesStatus
        methods['server_info'] = ServerInfoable().serverInfo
        
        rpcHandler.registerRpcMethods(methods)
        
        # Set up the socket poller
        self._poller = self._sockets.poller()
        self._poller.register(self._replySocket, self._sockets.POLLIN)
        
        self._logger.notice("Process monitor ready to handle requests")
        
    def _ping(self):
        """Ping the process monitor.
        
        Returns
        -------
        str
            A ping response containing the name of the process monitor
        """
        return "Process monitor %s" % self._name
        
    def _step(self):
        """Execute a single step of the control loop.
        
        Returns
        -------
        bool
            True if the operation was executed successfully
        """
        socks = dict(self._poller.poll(timeout=500))
        if self._replySocket in socks:
            try:
                self._sockets.rpc.handleRequest(self._replySocket)
                return True
            except Exception as e:
                trace = traceback.format_exc()
                self._logger.error(
                    "Error handling request: %s\n%s" % (str(e), trace))
        return False
        
    def run(self):
        """Run the process monitor loop."""
        self._logger.notice("Process monitor started")
        if self._timingStatistics:
            self._timingStatistics.setBenchmarkName(self._name)
            
        while not self._isTerminated:
            try:
                self._processMonitor.updateProcessesStatus()
                self._step()
            except KeyboardInterrupt:
                self._logger.notice("Keyboard interrupt received")
                self.terminate()
            except Exception as e:
                trace = traceback.format_exc()
                self._logger.error(
                    "Error in process monitor loop: %s\n%s" % (str(e), trace))
                time.sleep(1)
                
        self._logger.notice("Process monitor terminated")
        
    def terminate(self):
        """Terminate the process monitor."""
        if self._isTerminated:
            return
            
        self._logger.notice("Terminating")
        self._isTerminated = True
        self._sockets.close()
        self._timingStatistics = None 