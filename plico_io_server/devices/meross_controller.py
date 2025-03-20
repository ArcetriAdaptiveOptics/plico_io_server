import asyncio
import os
import threading
import time
from plico.utils.logger import Logger
from plico.utils.decorator import override
from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager


class MerossController:
    '''
    Meross smart plug controller implementation
    '''
    
    def __init__(self, name='MerossController', email=None, password=None, model='MSS425E', api_base_url='https://iotx-eu.meross.com', simulation_mode=False, **_):
        self._name = name
        self._logger = Logger.of('MerossController')
        self._email = email
        self._password = password
        self._api_base_url = api_base_url
        self._simulation_mode = simulation_mode
        self._model = model
        self._devices = {}
        self._manager = None
        self._http_client = None
        self._loop = None
        self._thread = None
        self._initialized = False
        
        if not self._simulation_mode:
            if email is None or password is None:
                self._logger.error("Email and password are required for Meross controller")
                self._logger.notice("Falling back to simulation mode")
                self._simulation_mode = True
            else:
                self._initialize_async_loop()
        
        if self._simulation_mode:
            self._logger.notice("Running in simulation mode")
            # Create simulated devices
            self._devices = {
                "simulated1": {"name": "Simulated Plug 1", "status": False},
                "simulated2": {"name": "Simulated Plug 2", "status": False}
            }
    
    def _initialize_async_loop(self):
        """Initialize the async event loop in a background thread"""
        if os.name == 'nt':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
        
        self._loop = asyncio.new_event_loop()
        
        # Start the event loop in a separate thread
        self._thread = threading.Thread(target=self._run_event_loop, daemon=True)
        self._thread.start()
        
        # Give the event loop time to start
        time.sleep(1)
        
        # Initialize the client and manager
        future = asyncio.run_coroutine_threadsafe(self._initialize_client(), self._loop)
        try:
            future.result(timeout=10)  # Wait up to 10 seconds
            self._initialized = True
            self._logger.notice("Meross controller initialized")
        except asyncio.TimeoutError:
            self._logger.error("Timeout initializing Meross client")
            self._simulation_mode = True
        except Exception as e:
            self._logger.error(f"Error initializing Meross client: {str(e)}")
            self._simulation_mode = True
    
    def _run_event_loop(self):
        """Run the asyncio event loop in a background thread"""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
    
    async def _initialize_client(self):
        """Initialize the Meross HTTP client and manager"""
        try:
            self._http_client = await MerossHttpClient.async_from_user_password(
                api_base_url=self._api_base_url,
                email=self._email,
                password=self._password
            )
            
            self._manager = MerossManager(http_client=self._http_client)
            await self._manager.async_init()
            
            # Discover devices
            await self._manager.async_device_discovery()
            
            # Give devices time to show up
            await asyncio.sleep(2)
            
            # Update devices dictionary
            for device in self._manager.find_devices():
                await device.async_update()
                self._devices[device.uuid] = device
                
            self._logger.notice(f"Found {len(self._devices)} Meross devices")
        except Exception as e:
            self._logger.error(f"Failed to initialize Meross controller: {str(e)}")
            raise
    
    def name(self):
        """Get the name of the controller"""
        return self._name
    
    def terminate(self):
        """Terminate the controller instance"""
        return self.deinitialize()
    
    def deinitialize(self):
        """Clean up resources"""
        if not self._simulation_mode and self._initialized:
            # Run the cleanup in the async loop
            future = asyncio.run_coroutine_threadsafe(self._cleanup(), self._loop)
            try:
                future.result(timeout=5)
            except Exception as e:
                self._logger.error(f"Error during cleanup: {str(e)}")
            
            # Stop the event loop
            self._loop.call_soon_threadsafe(self._loop.stop)
            if self._thread:
                self._thread.join(timeout=5)
    
    async def _cleanup(self):
        """Clean up the Meross manager and client"""
        if self._manager:
            self._manager.close()
        if self._http_client:
            await self._http_client.async_logout()
    
    def _get_device(self, device_id=None):
        """Get a device by ID or the first available device"""
        if self._simulation_mode:
            if device_id is None:
                # Return the first simulated device
                device_id = next(iter(self._devices))
            return device_id if device_id in self._devices else None
        
        if device_id is None:
            # Return the first real device
            if len(self._devices) > 0:
                return next(iter(self._devices))
            return None
        
        return device_id if device_id in self._devices else None
    
    def turnOn(self, device_id=None, channel=0):
        """Turn on a device (method required by Controller)"""
        self._logger.notice(f"Turning on device {device_id}, channel {channel}")
        
        if self._simulation_mode:
            device_id = self._get_device(device_id)
            if device_id:
                self._devices[device_id]["status"] = True
                return True
            return False
        
        if not self._initialized:
            self._logger.error("Meross controller not initialized")
            return False
        
        device_id = self._get_device(device_id)
        if device_id:
            device = self._devices[device_id]
            future = asyncio.run_coroutine_threadsafe(
                device.async_turn_on(channel=channel), 
                self._loop
            )
            try:
                future.result(timeout=5)
                return True
            except Exception as e:
                self._logger.error(f"Error turning on device: {str(e)}")
                return False
        
        self._logger.error("No device found")
        return False
    
    def turnOff(self, device_id=None, channel=0):
        """Turn off a device (method required by Controller)"""
        self._logger.notice(f"Turning off device {device_id}, channel {channel}")
        
        if self._simulation_mode:
            device_id = self._get_device(device_id)
            if device_id:
                self._devices[device_id]["status"] = False
                return True
            return False
        
        if not self._initialized:
            self._logger.error("Meross controller not initialized")
            return False
        
        device_id = self._get_device(device_id)
        if device_id:
            device = self._devices[device_id]
            future = asyncio.run_coroutine_threadsafe(
                device.async_turn_off(channel=channel), 
                self._loop
            )
            try:
                future.result(timeout=5)
                return True
            except Exception as e:
                self._logger.error(f"Error turning off device: {str(e)}")
                return False
        
        self._logger.error("No device found")
        return False
    
    def getStatus(self):
        """Get the current status (method required by Controller)"""
        status = {
            "name": self._name,
            "model": self._model,
            "simulation_mode": self._simulation_mode,
            "initialized": self._initialized,
            "device_count": len(self._devices),
            "devices": {}
        }
        
        # Add device statuses
        for device_id, device in self._devices.items():
            if self._simulation_mode:
                status["devices"][device_id] = {
                    "name": device["name"],
                    "status": device["status"]
                }
            else:
                try:
                    if self._initialized:
                        future = asyncio.run_coroutine_threadsafe(
                            device.async_update(), 
                            self._loop
                        )
                        future.result(timeout=2)
                    
                    status["devices"][device_id] = {
                        "name": device.name,
                        "status": device.is_on()
                    }
                except Exception as e:
                    self._logger.error(f"Error getting device status: {str(e)}")
                    status["devices"][device_id] = {
                        "name": "Unknown",
                        "status": False,
                        "error": str(e)
                    }
        
        return status
    
    def getSnapshot(self):
        """Get a snapshot of the controller state (method required by Controller)"""
        return self.getStatus()  # Same as getStatus for now 