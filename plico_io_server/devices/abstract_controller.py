from abc import ABC, abstractmethod


class AbstractController(ABC):
    '''
    Abstract base class for all controller devices.
    This defines the interface that all controller devices must implement.
    '''

    @abstractmethod
    def name(self):
        """
        Returns the name of the controller
        """
        pass

    @abstractmethod
    def deinitialize(self):
        """
        Release resources and cleanup
        """
        pass

    @abstractmethod
    def turn_on(self, device_id=None, channel=0):
        """
        Turn on a device
        
        Parameters:
        -----------
        device_id : str or None
            The ID of the device to turn on. If None, use the first available device.
        channel : int
            The channel to turn on (default: 0)
        """
        pass

    @abstractmethod
    def turn_off(self, device_id=None, channel=0):
        """
        Turn off a device
        
        Parameters:
        -----------
        device_id : str or None
            The ID of the device to turn off. If None, use the first available device.
        channel : int
            The channel to turn off (default: 0)
        """
        pass

    @abstractmethod
    def get_status(self, device_id=None, channel=0):
        """
        Get the current status of a device
        
        Parameters:
        -----------
        device_id : str or None
            The ID of the device to check. If None, use the first available device.
        channel : int
            The channel to check (default: 0)
            
        Returns:
        --------
        bool : True if the device is on, False if it's off
        """
        pass

    @abstractmethod
    def list_devices(self):
        """
        List all available devices
        
        Returns:
        --------
        dict : A dictionary of available devices with their IDs as keys
        """
        pass 