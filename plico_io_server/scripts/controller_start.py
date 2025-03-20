#!/usr/bin/env python
import sys
import signal
import os
import time
import subprocess
import argparse
import traceback
import psutil
import logging
from plico.utils.config_file_manager import ConfigFileManager
from plico.utils.configuration import Configuration
from plico.utils.logger import Logger
from plico.utils.decorator import override
from plico_io_server.utils.constants import Constants
from plico.utils.base_runner import BaseRunner
from plico.rpc.zmq_ports import ZmqPorts
from plico_io_server.controller.controller_runner import ControllerRunner


def is_process_running(process_name):
    """Check if a process is running by name.
    
    Parameters
    ----------
    process_name : str
        Name of the process to check
        
    Returns
    -------
    bool
        True if the process is running, False otherwise
    """
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'] == process_name:
                return True
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return False


def _parseArguments():
    """Parse command line arguments.
    
    Returns
    -------
    Namespace
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='Start controller server')
    parser.add_argument('--config',
                        type=str,
                        help='Server configuration file',
                        default=None)
    parser.add_argument('--server-only',
                        action='store_true',
                        help='Start only the server, not the process monitor',
                        default=False)
    parser.add_argument('--controller-name',
                        type=str,
                        help='Controller section name in configuration',
                        default='controller1')
    parser.add_argument('--controller-kwargs',
                        type=str,
                        help='Keyword arguments for the controller (json format)',
                        default=None)
    return parser.parse_args()


def main():
    """Start the controller server."""
    args = _parseArguments()
    
    # Initialize config
    cfgMgr = ConfigFileManager(
        Constants.APP_NAME,
        Constants.APP_AUTHOR,
        Constants.THIS_PACKAGE
    )
    
    # Install config file if needed
    cfgMgr.installConfigFileFromPackage()
    
    # Get config file path
    config_file = args.config or cfgMgr.getConfigFilePath()
    
    # Check if already running
    if is_process_running(Constants.SERVER_PROCESS_NAME):
        print('Server already running. Terminating.')
        return
        
    # Start process monitor if needed
    if not args.server_only:
        if not is_process_running(Constants.PROCESS_MONITOR_CONFIG_SECTION):
            print('Starting process monitor')
            try:
                env = os.environ.copy()
                if args.config:
                    env['PLICO_IO_CONFIG_FILE'] = args.config
                packageName = Constants.THIS_PACKAGE
                monitorStartScript = '%s.process_monitor.process_monitor_start' % packageName
                cmd = [sys.executable, '-m', monitorStartScript]
                
                subprocess.Popen(cmd,
                                   stdout=subprocess.PIPE,
                                   stderr=subprocess.PIPE,
                                   env=env)
                time.sleep(1)
            except Exception as e:
                print('Failed to start process monitor: %s' % str(e))
                traceback.print_exc()
                
    # Start controller server
    try:
        print('Starting controller server')
        
        # Create runner and start it with proper arguments
        runner = ControllerRunner()
        controller_section = args.controller_name
        sys.argv = [sys.argv[0], config_file, controller_section]
        print(f"Using controller section: {controller_section}")
        runner.start(sys.argv)
        
    except Exception as e:
        print('Error in controller server: %s' % str(e))
        traceback.print_exc()
        
    print('Controller server terminated')


if __name__ == '__main__':
    main() 