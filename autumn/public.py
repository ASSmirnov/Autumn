from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import wraps
from typing import Any, Type, dataclass_transform, LiteralString
from autumn.exceptions import AutomnConfigurationError

from autumn.helpers.type_hints import Collection, Optional
from .core.register import dependency_descrition

from .core.register import register, create_component, InjectableDependency, InjectableType
from .core.manager import dm
from .core.scope import SINGLETON, PROTOTYPE, SESSION as __SESSION, BaseCustomScope


@dataclass_transform()
def component(interface: Any | None = None,
              *, 
              scope: str, 
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


@dataclass
class _Dependency:
    interface: Any
    collection: Type | None = None
    optional: bool = False

def autowired_method(func):
    dependencies: dict[str, _Dependency] = {} 
    for name, original_type_hint in func.__annotations__.items():
        type_hint = dependency_descrition(original_type_hint)
        match type_hint:
            case (Optional(t), InjectableDependency(InjectableType.component)):
                dependency = _Dependency(interface=t,
                                        optional=True)
                dependencies[name] = dependency
            case (Collection(ct, t), InjectableDependency(InjectableType.component)):
                dependency = _Dependency(interface=t,
                                        collection=ct)
                dependencies[name] = dependency
            case (t, InjectableDependency(InjectableType.component)):
                dependency = _Dependency(interface=t)
                dependencies[name] = dependency
            case(_, InjectableDependency(InjectableType.property)):
                raise AutomnConfigurationError(f"Injectable properties are not supported for"
                                               "autowared methods yet")
            
    @wraps(func)
    def decorator(*args, **kwargs):
        kw: dict[str, Any] = {}
        for name, dependency in dependencies.items():
            if name in kwargs:
                continue
            elif dependency.collection:
                value = dm.get_instances(dependency.interface)
                value = dependency.collection(value)
            else:
                value = dm.get_instance(dependency.interface, optional=dependency.optional)
            kw[name] = value
        return func(*args, **{**kwargs, **kw})
    return decorator




def scope(name: LiteralString, profiles: tuple[str, ...] = ()):
    if not isinstance(name, str):
        raise AutomnConfigurationError("Scope name must be a string")
    def wrapper(cls):
        if not issubclass(cls, BaseCustomScope):
            raise AutomnConfigurationError("Scope must derive BaseSession")
        cls = component(scope=__SESSION,
                        interface=name,
                        profiles=profiles,
                        )(cls)
        return cls
    return wrapper

Injectable = InjectableDependency(type=InjectableType.component, args=())

def _property(name: str) -> InjectableDependency:
    return InjectableDependency(type=InjectableType.property, args=(name, ))


BaseCustomScope = BaseCustomScope
Property = _property
dm = dm
SINGLETON = SINGLETON
PROTOTYPE = PROTOTYPE