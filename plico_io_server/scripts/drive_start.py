#!/usr/bin/env python
import sys
import time
import os
import socket
import argparse
import logging
from plico.utils.control_loop import join_process_with_unknown_pid
from plico.utils.base_runner import BaseRunner
from plico.utils.decorator import override
from plico.utils.logger import Logger
from plico_io_server.process_monitor.runner import Runner as ProcessMonitorRunner
from plico_io_server.devices.runner import Runner as DeviceRunner
from plico_io_server.controller.runner import Runner as ControllerRunner
from plico_io_server.utils.constants import Constants
from plico_io_server.utils.zlog import ZmqPublisherForLogger


__version__ = "$Id: io_start.py 49 2018-04-10 12:28:27Z lbusoni $"


class Runner(BaseRunner):

    PROCESS_MONITOR_CONFIG_SECTION = Constants.PROCESS_MONITOR_CONFIG_SECTION
    CONTROLLER_CONFIG_SECTION = Constants.CONTROLLER_CONFIG_SECTION
    DEVICE_CONFIG_SECTION = Constants.DEVICE_CONFIG_SECTION
    SERVER_CONFIG_SECTION = Constants.SERVER_CONFIG_SECTION

    def __init__(self, argv):
        BaseRunner.__init__(self)
        self._argv = argv
        self._args = None
        self._substSystemsRunning = []
        self._logger = Logger.of("IO Server runner")
        self._zmqPublisher = None

    def _parseArguments(self):
        parser = argparse.ArgumentParser(
            description='''
            Start a 'IO' controller server using local terminals
            ''')
        parser.add_argument(
            '-d', '--config-directory',
            dest='config_directory',
            action='store',
            required=False,
            default=None,
            help='''
            Directory where to find configuration files.
            If not given, default is the code's source root directory.
            ''')
        parser.add_argument(
            '-c', '--config-file',
            dest='config_file',
            action='store',
            required=False,
            default="plico_io_server.conf",
            help='''
            Configuration file (without path).
            If not given, default is plico_io_server.conf.
            ''')
        parser.add_argument(
            '--kill', dest='kill',
            action='store_true',
            help='''
            Kill running processes and exit, no process is started
            ''')
        parser.add_argument(
            '--log-level',
            dest='log_level',
            action='store',
            default=logging.INFO,
            type=int,
            choices={logging.DEBUG,
                     logging.INFO,
                     logging.WARNING,
                     logging.ERROR,
                     logging.CRITICAL},
            help='''
            log level (e.g. logging.DEBUG, logging.INFO)
            ''')
        parser.add_argument(
            '--no-process-monitor',
            dest='no_process_monitor',
            action='store_true',
            help='''
            Do not execute the process monitor server
            ''')
        return parser.parse_args(self._argv)

    def _replyPort(self):
        hostname = socket.gethostname()
        socketAddr = self.configuration.value(
            self.SERVER_CONFIG_SECTION,
            'server_socket_address')
        return '%s:%s' % (hostname, socketAddr)

    def _setLogLevel(self):
        self._logger.setLevel(self._args.log_level)

    def _createZmqPublisher(self):
        addr = self.configuration.value(
            self.SERVER_CONFIG_SECTION,
            'log_socket_address')
        self._zmqPublisher = ZmqPublisherForLogger(addr)

    @override
    def _execute(self):
        self._args = self._parseArguments()
        self._setLogLevel()
        self._createConfigManager(
            self._args.config_directory,
            self._args.config_file)
        self._createZmqPublisher()

        if self._args.kill:
            self._killSubprocessesAndExit()

        self._logger.notice(
            "Starting IO server, reply to %s" %
            self._replyPort())

        if not self._args.no_process_monitor:
            self._startProcessMonitor()
        self._startDeviceContainer()
        self._startController()

        time.sleep(5)
        processesHaveStarted = (len(self._substSystemsRunning) > 0)
        if not processesHaveStarted:
            self._logger.warning(
                'No process started, exiting.')
            return
        self._logger.notice(
            'Subsystems started. Press Ctrl-C to terminate')
        try:
            time.sleep(float('inf'))
        except KeyboardInterrupt:
            self._logger.notice("IO server closing")

    def _killSubprocessesAndExit(self):
        self._logger.notice("Removing previously running IO server")

        if not self._args.no_process_monitor:
            ProcessMonitorRunner.terminateExisting(
                self.configuration,
                self.PROCESS_MONITOR_CONFIG_SECTION,
                "Process Monitor")

        DeviceRunner.terminateExisting(
            self.configuration,
            self.DEVICE_CONFIG_SECTION,
            "IO Devices")

        try:
            ControllerRunner.terminateExisting(self.configuration,
                                             self.CONTROLLER_CONFIG_SECTION,
                                             "IO Server Controller")
        except Exception as e:
            self._logger.error("Cannot terminate controller: %s" % str(e))

        sys.exit("Terminated already running processes")

    def _startProcessMonitor(self):
        serverMonitor = ProcessMonitorRunner()
        serverMonitor.start(
            self.configuration,
            self.PROCESS_MONITOR_CONFIG_SECTION)
        self._substSystemsRunning.append(serverMonitor)

    def _startDeviceContainer(self):
        device = DeviceRunner()
        device.start(
            self.configuration,
            self.DEVICE_CONFIG_SECTION)
        self._substSystemsRunning.append(device)

    def _startController(self):
        server = ControllerRunner()
        server.start(
            self.configuration,
            self.CONTROLLER_CONFIG_SECTION,
            logLevel=self._args.log_level)
        self._substSystemsRunning.append(server)


def main():
    """
    Start a IO server, including controller server, 
    devices server, and process monitor.
    """
    runner = Runner(sys.argv[1:])
    runner.run()


if __name__ == '__main__':
    main() 