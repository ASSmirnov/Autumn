from dataclasses import dataclass
from typing import Any

from .core.register import register, create_component, InjectableProperty, Injectable
from .core.manager import dm
from .core.scope import SINGLETON, PROTOTYPE


def component(*, 
              scope: str, 
              interface: Any | None = None,
              profiles: tuple[str, ...] = ()):
    def decorator(cls):
        component = create_component(interface=interface,
                                     scope=scope,
                                     profiles=profiles,
                                     cls=cls)

        component_class = dataclass(cls,
                                    eq=False, 
                                    order=False, 
                                    match_args=False, 
                                    slots=True, 
                                    frozen=True)
        component.cls = component_class
        register.register_component(component)
        return component_class
    return decorator

Injectable = Injectable
Property = InjectableProperty
dm = dm
SINGLETON = SINGLETON
PROTOTYPE = PROTOTYPE