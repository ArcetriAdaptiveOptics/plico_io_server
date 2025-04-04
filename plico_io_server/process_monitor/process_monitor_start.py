#!/usr/bin/env python
import sys
from plico.utils.config_file_manager import ConfigFileManager
# Use the standard ProcessMonitorRunner from plico.utils
from plico.utils.process_monitor_runner import ProcessMonitorRunner
# Use constants specifically from plico_io_server
from plico_io_server.utils.constants import Constants


def main():
    """Initializes and starts the ProcessMonitorRunner for plico_io_server."""
    # Define the prefix for controller sections (e.g., 'controller1', 'controller2')
    # This must match the sections in plico_io_server.conf that define controllers.
    controller_prefix = 'controller'

    # Instantiate the standard runner
    # Constants.SERVER_PROCESS_NAME ('plico_io_server') is the base name of the script
    # that the monitor will call to start individual controllers.
    # default_server_config_prefix tells the runner to look for sections starting
    # with 'controller' in the config file.
    runner = ProcessMonitorRunner(Constants.SERVER_PROCESS_NAME,
                                  default_server_config_prefix=controller_prefix)

    # Correctly initialize ConfigFileManager for plico_io_server
    configFileManager = ConfigFileManager(Constants.APP_NAME,
                                          Constants.APP_AUTHOR,
                                          Constants.THIS_PACKAGE)

    # Ensure the default config file is installed if it doesn't exist
    configFileManager.installConfigFileFromPackage()

    # Prepare arguments for the runner's start method:
    # argv[0]: script name (can be empty)
    # argv[1]: path to the configuration file
    # argv[2]: section name for the process monitor itself in the config file
    argv = ['',
            configFileManager.getConfigFilePath(),
            Constants.PROCESS_MONITOR_CONFIG_SECTION]

    # Start the runner and exit with its status code
    sys.exit(runner.start(argv))


if __name__ == '__main__':
    main() 