class Constants:
    """Constants used throughout the package."""
    
    # Application name and author
    APP_NAME = 'inaf.arcetri.ao.plico_io_server'
    APP_AUTHOR = 'INAF Arcetri Adaptive Optics'
    THIS_PACKAGE = 'plico_io_server'
    
    # Process names
    SERVER_PROCESS_NAME = 'plico_io_server'
    PROCESS_MONITOR_CONFIG_SECTION = 'processMonitor'
    CONTROLLER_CONFIG_SECTION = 'controller1'
    DEVICE_CONFIG_SECTION = 'deviceMeross'
    SERVER_CONFIG_SECTION = 'global'
    
    # Configuration sections
    DEFAULT_SERVER_CONFIG_SECTION_PREFIX = 'plico_io_server'
    
    # Device types
    DEVICE_TYPE_MEROSS = 'meross'

    # Must be the same as console_scripts in setup.py
    START_PROCESS_NAME = 'plico_io_start'
    STOP_PROCESS_NAME = 'plico_io_stop'
    KILL_ALL_PROCESS_NAME = 'plico_io_kill_all' 