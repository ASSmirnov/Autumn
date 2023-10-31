from contextlib import contextmanager
from dataclasses import dataclass
from types import MappingProxyType
from typing import Any, LiteralString, Mapping, Self, Type, TypeVar

from autumn.core.scope import clear_caches

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

    def init_property(self, property_name: LiteralString, value: Any) -> None:
        self._config.properties[property_name] = value

    def init_profiles(self, *profiles: LiteralString) -> None:
        for profile in profiles:
            self._config.active_profiles.append(profile)

    def start(self):
        clear_caches()
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
        self._started: bool = False
        self.test_mode: bool = False
 
    def init_property(self, property_name: LiteralString, value: Any) -> None:
        if self._started:
            raise AutomnConfigurationError("Attempt to initialize property after dm start")
        self._instance.init_property(property_name, value)
    
    def init_profiles(self, *profiles: LiteralString) -> None:
        if self._started:
            raise AutomnConfigurationError("Attempn to initialize profile after dm start")
        self._instance.init_profiles(*profiles)
    
    def init(self, test_mode=False) -> None:
        if self._started:
            raise AutomnConfigurationError("Attempn to initialize dm after start")
        self.test_mode = test_mode
    
    @contextmanager
    def copy(self) -> None:
        if not self.test_mode:
            raise AutomnConfigurationError("Attempt to stash frozen dm")
        config = self._instance.get_config() 
        self._started = False
        self._instance = _ManagerInstance(config=config.copy())
        yield
        self._started = False
        self._instance = _ManagerInstance(config=config)
        self.start()
    
    @contextmanager
    def clear(self) -> None:
        if not self.test_mode:
            raise AutomnConfigurationError("Attempt to stash frozen dm")
        self._started = False
        config = self._instance.get_config() 
        self._instance = _ManagerInstance()
        yield
        self._started = False
        self._instance = _ManagerInstance(config=config)
        self.start()

    
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