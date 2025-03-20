#!/usr/bin/env python
import sys
import subprocess
import argparse
import traceback
from plico.utils.config_file_manager import ConfigFileManager
from plico.utils.logger import Logger
from plico.utils.control_utilities import ControlUtilities
from plico_controller_server.utils.constants import Constants


def _parseArguments():
    """Parse command line arguments.
    
    Returns
    -------
    Namespace
        Parsed command line arguments
    """
    parser = argparse.ArgumentParser(description='Stop controller server')
    parser.add_argument('--config',
                        type=str,
                        help='Server configuration file',
                        default=None)
    parser.add_argument('--kill',
                        action='store_true',
                        help='Kill the process instead of stopping it gracefully',
                        default=False)
    parser.add_argument('--server-only',
                        action='store_true',
                        help='Stop only the server, not the process monitor',
                        default=False)
    return parser.parse_args()


def main():
    """Stop the controller server."""
    args = _parseArguments()
    
    # Initialize config
    cfgMgr = ConfigFileManager(args.config)
    
    # Set up logger
    logLevel = cfgMgr.value(Constants.STOP_PROCESS_NAME, 'logLevel')
    logger = Logger.of(Constants.STOP_PROCESS_NAME)
    logger.setLevel(logLevel)
    
    logger.notice('Stopping controller server')
    
    def stop_process(name):
        """Stop a process by name."""
        logger.notice(f'Stopping {name}')
        try:
            if args.kill:
                ControlUtilities.killProcessByName(name)
            else:
                ControlUtilities.stopProcessByName(name)
        except Exception as e:
            logger.error(f'Failed to stop {name}: {str(e)}')
            traceback.print_exc()
    
    # Stop controller server
    stop_process(Constants.SERVER_PROCESS_NAME)
    
    # Stop process monitor if requested
    if not args.server_only:
        stop_process(Constants.PROCESS_MONITOR_CONFIG_SECTION)
    
    logger.notice('Stop command completed')


if __name__ == '__main__':
    main() 