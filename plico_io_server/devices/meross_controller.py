import asyncio
import os
import threading
import time
from plico.utils.logger import Logger
from plico.utils.decorator import override
from meross_iot.http_api import MerossHttpClient
from meross_iot.manager import MerossManager
from meross_iot.model.enums import OnlineStatus


class MerossController:
    '''
    Meross smart plug controller implementation
    '''
    
    def __init__(self, name='MerossController', email=None, password=None, model=None, api_base_url='https://iotx-eu.meross.com', simulation_mode=False, **_):
        self._name = name
        self._logger = Logger.of(f'MerossController({name} - {model})')
        self._email = email
        self._password = password
        self._api_base_url = api_base_url
        self._simulation_mode = simulation_mode
        self._model = model
        self._target_device = None
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
            elif model is None:
                self._logger.error("Model (device_type) is required for Meross controller")
                self._logger.notice("Falling back to simulation mode")
                self._simulation_mode = True
            else:
                self._initialize_async_loop()
        
        if self._simulation_mode:
            self._logger.notice("Running in simulation mode")
            self._target_device = {
                "name": self._name or f"Simulated {self._model or 'Device'}",
                "model": self._model or "simulated",
                "status": False,
                "online": True
            }
            self._initialized = True
    
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
            future.result(timeout=15)
            self._initialized = True
            self._logger.notice(f"Meross controller initialized. Target device found: {self._target_device is not None}")
            if not self._target_device:
                self._logger.error(f"Could not find a Meross device matching model '{self._model}'")
        except asyncio.TimeoutError:
            self._logger.error("Timeout initializing Meross client or finding device")
            self._simulation_mode = True
        except Exception as e:
            self._logger.error(f"Error initializing Meross client: {str(e)}")
            self._simulation_mode = True
    
    def _run_event_loop(self):
        """Run the asyncio event loop in a background thread"""
        asyncio.set_event_loop(self._loop)
        self._loop.run_forever()
    
    async def _initialize_client(self):
        """Initialize the Meross HTTP client, manager, and find the target device."""
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
            await asyncio.sleep(5)
            
            found_devices = self._manager.find_devices()
            self._logger.notice(f"Found {len(found_devices)} Meross devices associated with the account.")
            
            for device in found_devices:
                # Perform case-insensitive comparison
                device_type_lower = getattr(device, 'type', '').lower()
                target_model_lower = (self._model or '').lower()

                if device_type_lower and target_model_lower and device_type_lower.startswith(target_model_lower):
                    await device.async_update() # Get latest state
                    if self._target_device is None:
                        self._target_device = device
                        self._logger.notice(f"Target device found: Name='{device.name}', Type='{device.type}', UUID='{device.uuid}'")
                    else:
                        self._logger.warning(f"Found multiple devices matching model '{self._model}'. Using the first one found: '{self._target_device.name}'.")
                        break
            
            if self._target_device is None:
                self._logger.error(f"No online device found matching model type '{self._model}'. Available devices: {[(d.name, d.type, d.online_status) for d in found_devices]}")
        except Exception as e:
            self._logger.error(f"Failed during Meross client/device initialization: {str(e)}")
            if self._manager:
                self._manager.close()
            if self._http_client:
                await self._http_client.async_logout()
            self._http_client = None
            self._manager = None
            raise
    
    def name(self):
        """Get the name of the controller"""
        return self._name
    
    def terminate(self):
        """Terminate the controller instance"""
        return self.deinitialize()
    
    def deinitialize(self):
        """Clean up resources"""
        if self._loop and self._loop.is_running():
            if not self._simulation_mode and self._initialized:
                future = asyncio.run_coroutine_threadsafe(self._cleanup(), self._loop)
                try:
                    future.result(timeout=5)
                except Exception as e:
                    self._logger.error(f"Error during cleanup: {str(e)}")
            
            self._loop.call_soon_threadsafe(self._loop.stop)
        if self._thread and self._thread.is_alive():
            self._thread.join(timeout=5)
            if self._thread.is_alive():
                self._logger.warning("Event loop thread did not terminate cleanly.")
        
        self._initialized = False
    
    async def _cleanup(self):
        """Clean up the Meross manager and client"""
        if self._manager:
            self._manager.close()
            self._manager = None
        if self._http_client:
            try:
                await self._http_client.async_logout()
            except Exception as e:
                self._logger.error(f"Error logging out http client: {e}")
            self._http_client = None
    
    def turnOn(self, channel=0):
        """Turn on the target device."""
        if not self._target_device:
            self._logger.error(f"Cannot turn on: No target device '{self._model}' found or initialized.")
            return False
        
        self._logger.notice(f"Turning on target device (Channel: {channel})")
        
        if self._simulation_mode:
            self._target_device["status"] = True
            self._logger.notice(f"Simulated device '{self._target_device['name']}' turned ON.")
            return True
        
        if not self._initialized or not self._loop or not self._loop.is_running():
            self._logger.error("Cannot turn on: Meross controller not initialized or event loop stopped.")
            return False
        
        future = asyncio.run_coroutine_threadsafe(
            self._target_device.async_turn_on(channel=channel),
            self._loop
        )
        try:
            result = future.result(timeout=10)
            self._logger.notice(f"Turn ON command successful for '{self._target_device.name}'.")
            return result if result is not None else True
        except Exception as e:
            self._logger.error(f"Error turning ON target device '{self._target_device.name}': {str(e)}")
            return False
    
    def turnOff(self, channel=0):
        """Turn off the target device."""
        if not self._target_device:
            self._logger.error(f"Cannot turn off: No target device '{self._model}' found or initialized.")
            return False
        
        self._logger.notice(f"Turning off target device (Channel: {channel})")
        
        if self._simulation_mode:
            self._target_device["status"] = False
            self._logger.notice(f"Simulated device '{self._target_device['name']}' turned OFF.")
            return True
        
        if not self._initialized or not self._loop or not self._loop.is_running():
            self._logger.error("Cannot turn off: Meross controller not initialized or event loop stopped.")
            return False
        
        future = asyncio.run_coroutine_threadsafe(
            self._target_device.async_turn_off(channel=channel),
            self._loop
        )
        try:
            result = future.result(timeout=10)
            self._logger.notice(f"Turn OFF command successful for '{self._target_device.name}'.")
            return result if result is not None else True
        except Exception as e:
            self._logger.error(f"Error turning OFF target device '{self._target_device.name}': {str(e)}")
            return False
    
    def getStatus(self):
        """Get the current status of the target device."""
        status = {
            "controller_name": self._name,
            "target_model": self._model,
            "simulation_mode": self._simulation_mode,
            "initialized": self._initialized,
            "target_device_status": {}
        }
        
        target_status = {
            "name": "N/A",
            "model": self._model,
            "online": False,
            "status": False,
            "error": None
        }
        
        if self._simulation_mode:
            if self._target_device:
                target_status["name"] = self._target_device["name"]
                target_status["online"] = self._target_device["online"]
                target_status["status"] = self._target_device["status"]
            else:
                target_status["error"] = "Simulation device not created"
        elif self._initialized and self._target_device and self._loop and self._loop.is_running():
            try:
                future = asyncio.run_coroutine_threadsafe(
                    self._target_device.async_update(),
                    self._loop
                )
                future.result(timeout=5)
                
                target_status["name"] = getattr(self._target_device, 'name', 'N/A')
                target_status["online"] = getattr(self._target_device, 'online_status', OnlineStatus.UNKNOWN) == OnlineStatus.ONLINE
                target_status["status"] = self._target_device.is_on() if hasattr(self._target_device, 'is_on') else False
            except Exception as e:
                self._logger.error(f"Error getting target device status: {str(e)}")
                target_status["error"] = str(e)
                target_status["name"] = getattr(self._target_device, 'name', 'N/A')
                target_status["online"] = getattr(self._target_device, 'online_status', OnlineStatus.UNKNOWN) == OnlineStatus.ONLINE
        elif not self._initialized:
            target_status["error"] = "Controller not initialized"
        elif not self._target_device:
            target_status["error"] = f"Target device matching model '{self._model}' not found"
        elif not self._loop or not self._loop.is_running():
            target_status["error"] = "Async event loop not running"
        
        status["target_device_status"] = target_status
        return status
    
    def getSnapshot(self, prefix=''):
        """Get a snapshot of the controller state."""
        raw_status = self.getStatus()
        if not prefix:
            return raw_status
        
        snapshot = {}
        for key, value in raw_status.items():
            if isinstance(value, dict):
                for sub_key, sub_value in value.items():
                    snapshot[f"{prefix}.{key}.{sub_key}"] = sub_value
            else:
                snapshot[f"{prefix}.{key}"] = value
        return snapshot 