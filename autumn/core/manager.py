from contextlib import contextmanager
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, Mapping, Self, Type, TypeVar

from autumn.core.scope import clear_caches, restore_caches

from .register import Register, create_register_instance
from autumn.exceptions import AutomnComponentNotFound, AutomnConfigurationError


@dataclass
class Config:
    active_profiles: list[str]
    properties: dict[str, Any]

    def copy(self) -> Self:
        return Config(active_profiles=self.active_profiles[:],
                    properties=self.properties.copy())

_T = TypeVar("_T")


class _ManagerInstance:

    def __init__(self, config: Config | None = None) -> None:
        self._register: Register | None = None
        self._config: Config = config or Config(active_profiles=[], 
                                      properties={})
        self.properties: Mapping[str, Any] | None = None  

    def init_property(self, property_name: str, value: Any) -> None:
        self._config.properties[property_name] = value

    def init_profiles(self, *profiles: str) -> None:
        for profile in profiles:
            self._config.active_profiles.append(profile)

    def start(self):
        self._register = create_register_instance(self._config.active_profiles,
                                                  self._config.properties.keys())
        self.properties = MappingProxyType(self._config.properties)

    def get_instance(self, interface: _T, optional: bool = False) -> _T:
        return self._register.get_instance(interface, 
                                           self.properties or {},
                                           optional)

    def get_instances(self, interface: _T) -> list[_T]:
        return self._register.get_instances(interface, self.properties or {})
    
    def get_config(self) -> Config:
        return self._config


class _Manager:

    def __init__(self) -> None:
        self._instance = _ManagerInstance()
        self._instance_stack: list[_ManagerInstance] = []
        self._started: bool = False
 
    def init_property(self, property_name: str, value: Any) -> None:
        if self._started:
            raise AutomnConfigurationError("Attempt to initialize property after dm start")
        self._instance.init_property(property_name, value)
    
    def init_profiles(self, *profiles: str) -> None:
        if self._started:
            raise AutomnConfigurationError("Attempn to initialize profile after dm start")
        self._instance.init_profiles(*profiles)
    
    
    @contextmanager
    def clear(self, 
              *,
              copy_profiles: bool = False,
              copy_properties: bool = False,
              ) -> None:
        self._started = False
        self._instance_stack.append(self._instance)
        config = self._instance.get_config()
        new_config = Config()
        if copy_profiles:
            new_config.active_profiles = config.active_profiles[:]
        if copy_properties:
            new_config.properties = config.properties.copy()
        self._instance = _ManagerInstance(new_config)
        clear_caches()
        yield
        self._instance = self._instance_stack.pop()
        self._started = True
        restore_caches()

    
    def start(self) -> None:
        if self._started:
            raise AutomnConfigurationError("Attempn to start dm after start")
        self._instance.start()
        self._started = True
    
    def get_instance(self, interface: _T, optional: bool=False):
        if not self._started:
            raise AutomnConfigurationError("Attempn to get instance before dm start")
        return self._instance.get_instance(interface, optional)

    def get_instances(self, interface: _T) -> list[_T]:
        if not self._started:
            raise AutomnConfigurationError("Attempn to get instance before dm start")
        return self._instance.get_instances(interface)

    def get_property(self, name) -> Any:
        if name in self._instance.properties:
            return self._instance.properties[name]
        raise AutomnComponentNotFound()
    
dm = _Manager()