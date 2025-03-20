#!/usr/bin/env python
import sys
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
    parser = argparse.ArgumentParser(description='Kill all controller processes')
    parser.add_argument('--config',
                        type=str,
                        help='Server configuration file',
                        default=None)
    return parser.parse_args()


def main():
    """Kill all controller processes."""
    args = _parseArguments()
    
    # Initialize config
    cfgMgr = ConfigFileManager(args.config)
    
    # Set up logger
    logLevel = cfgMgr.value(Constants.KILL_ALL_PROCESS_NAME, 'logLevel')
    logger = Logger.of(Constants.KILL_ALL_PROCESS_NAME)
    logger.setLevel(logLevel)
    
    logger.notice('Killing all controller processes')
    
    # Kill all controller processes
    try:
        ControlUtilities.killProcessByName(Constants.SERVER_PROCESS_NAME)
        logger.notice(f'Killed {Constants.SERVER_PROCESS_NAME}')
    except Exception as e:
        logger.error(f'Failed to kill {Constants.SERVER_PROCESS_NAME}: {str(e)}')
        
    try:
        ControlUtilities.killProcessByName(Constants.PROCESS_MONITOR_CONFIG_SECTION)
        logger.notice(f'Killed {Constants.PROCESS_MONITOR_CONFIG_SECTION}')
    except Exception as e:
        logger.error(f'Failed to kill {Constants.PROCESS_MONITOR_CONFIG_SECTION}: {str(e)}')
        
    try:
        ControlUtilities.killProcessByName(Constants.START_PROCESS_NAME)
        logger.notice(f'Killed {Constants.START_PROCESS_NAME}')
    except Exception as e:
        logger.error(f'Failed to kill {Constants.START_PROCESS_NAME}: {str(e)}')
        
    try:
        ControlUtilities.killProcessByName(Constants.STOP_PROCESS_NAME)
        logger.notice(f'Killed {Constants.STOP_PROCESS_NAME}')
    except Exception as e:
        logger.error(f'Failed to kill {Constants.STOP_PROCESS_NAME}: {str(e)}')
        
    logger.notice('Kill all command completed')


if __name__ == '__main__':
    main() 