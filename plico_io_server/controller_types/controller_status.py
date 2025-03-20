from plico.utils.decorator import override
from plico.utils.snapshotable import Snapshotable


class ControllerStatus(Snapshotable):
    """Status class for controller server."""
    
    def __init__(self, name, devices=None):
        """Create a controller status.
        
        Parameters
        ----------
        name : str
            Name of the controller
        devices : dict, optional
            Dictionary of available devices
        """
        self._name = name
        self._devices = devices or {}
    
    @override
    def name(self):
        """Get the controller name.
        
        Returns
        -------
        str
            The controller name
        """
        return self._name
    
    @override
    def getSnapshot(self, prefix):
        """Get a snapshot of the controller status.
        
        Parameters
        ----------
        prefix : str
            Prefix for the snapshot keys
            
        Returns
        -------
        dict
            Dictionary containing the controller status
        """
        snapshot = {
            'name': self._name,
            'devices': self._devices
        }
        return self.prepend(prefix, snapshot) 