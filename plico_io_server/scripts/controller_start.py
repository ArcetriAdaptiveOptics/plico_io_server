#!/usr/bin/env python
import sys
# Removed unused imports

# Import the specific runner for plico_io_server controllers
from plico_io_server.controller.controller_runner import ControllerRunner


def main():
    """Instantiates the IO ControllerRunner and starts it, 
       relying on the base runner to parse arguments.
    """
    runner = ControllerRunner()
    # Pass sys.argv directly to the base runner's start method
    # which handles parsing positional config file and section name.
    sys.exit(runner.start(sys.argv))


if __name__ == '__main__':
    main() 