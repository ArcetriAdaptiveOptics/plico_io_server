#!/usr/bin/env python
import os
import sys
import time
import traceback
import argparse
from plico.utils.config_file_manager import ConfigFileManager
from plico.utils.logger import Logger
from plico.utils.control_utilities import ControlUtilities
from plico.utils.killer import Killer
from plico_controller_server.utils.constants import Constants
from plico.rpc.zmq_ports import ZmqPorts


def _parseArguments():
    """Parse command line arguments.
    
    Returns
    -------
    Namespace
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='Start process monitor')
    parser.add_argument('--config',
                        type=str,
                        help='Server configuration file',
                        default=None)
    return parser.parse_args()


def main():
    """Start the process monitor."""
    args = _parseArguments()
    
    # Initialize config
    cfgMgr = ConfigFileManager(args.config)
    
    # Set up logger
    logLevel = cfgMgr.value(Constants.PROCESS_MONITOR_CONFIG_SECTION, 'logLevel')
    logger = Logger.of(Constants.PROCESS_MONITOR_CONFIG_SECTION)
    logger.setLevel(logLevel)
    
    # Check if already running
    if ControlUtilities.isProcessRunning(Constants.PROCESS_MONITOR_CONFIG_SECTION):
        logger.notice('Process monitor already running. Terminating.')
        return
        
    # Start process monitor
    try:
        logger.notice('Starting process monitor')
        
        # Import the runner class
        from plico_controller_server.process_monitor.process_monitor_runner import ProcessMonitorRunner
        
        # Get process monitor configuration
        section = Constants.PROCESS_MONITOR_CONFIG_SECTION
        zmqPorts = ZmqPorts.fromConfig(cfgMgr, section)
        
        # Create runner
        runner = ProcessMonitorRunner(section, zmqPorts)
        
        # Set signal handlers and start runner
        killer = Killer()
        runner.run()
        runner.terminate()
        
    except Exception as e:
        logger.error('Error in process monitor: %s' % str(e))
        traceback.print_exc()
        
    logger.notice('Process monitor terminated')


if __name__ == '__main__':
    main() 