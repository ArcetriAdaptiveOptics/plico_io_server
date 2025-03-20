#!/usr/bin/env python
import sys
import os
import time
import subprocess
import shlex
from plico.utils.base_runner import BaseRunner
from plico.utils.decorator import override
from plico.utils.logger import Logger
from plico_io_server.utils.constants import Constants


__version__ = "$Id: io_stop.py 23 2018-01-27 10:18:48Z lbusoni $"


class Runner(BaseRunner):

    def __init__(self):
        BaseRunner.__init__(self)
        self._logger = Logger.of('IO stop')

    @override
    def _execute(self):
        self._createConfigManager()
        self._killProcesses()

    def _killProcesses(self):
        sectionsToKill = [
            Constants.PROCESS_MONITOR_CONFIG_SECTION,
            Constants.DEVICE_CONFIG_SECTION,
            Constants.CONTROLLER_CONFIG_SECTION,
        ]

        for sect in sectionsToKill:
            if sect == Constants.PROCESS_MONITOR_CONFIG_SECTION:
                pidfilepath = self.configuration.value(
                    sect, 'pidfile')
            else:
                pidfilepath = self.configuration.value(
                    sect, 'server_pidfile')
            if os.path.exists(pidfilepath):
                with open(pidfilepath, 'r') as pidfile:
                    pidToKill = int(pidfile.read())
                    cmd = "kill %d" % pidToKill
                    self._logger.notice(
                        "Executing command %s" % cmd)
                    subprocess.Popen(shlex.split(cmd))
            else:
                self._logger.warning(
                    "Cannot find pidfile %s for section %s" %
                    (pidfilepath, sect))

        self._logger.notice("Done")


def main():
    """
    Kill all processes related to Plico IO
    (controller, devices, process monitor).
    """
    runner = Runner()
    runner.run()


if __name__ == '__main__':
    main() 