from dataclasses import dataclass
from functools import wraps
from typing import Any, Type, dataclass_transform
from autumn.exceptions import AutomnConfigurationError

from autumn.helpers.type_hints import Annotated, Collection, Optional, Particular, extract_from_hint

from .core.register import register, create_component, InjectableProperty, InjectableDependency
from .core.manager import dm
from .core.scope import SINGLETON, PROTOTYPE, BaseSession


@dataclass_transform()
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


@dataclass
class _Dependency:
    interface: Any
    collection: Type | None = None
    optional: bool = False

def autowired_method(func):
    dependencies: dict[str, _Dependency] = {} 
    for name, original_type_hint in func.__annotations__.items():
        type_hint = extract_from_hint(original_type_hint)
        match type_hint:
            case Annotated(Optional(Particular(t)), (Particular(InjectableDependency()),)):
                dependency = _Dependency(interface=t,
                                        collection=None,
                                        optional=True)
                dependencies[name] = dependency
            case Annotated(Particular(t), (Particular(InjectableDependency()),)):
                dependency = _Dependency(interface=t,
                                        collection=None,
                                        optional=False)
                dependencies[name] = dependency
            case Annotated(Collection(ct, Particular(t)), (Particular(InjectableDependency()),)):
                dependency = _Dependency(interface=t,
                                        collection=ct,
                                        optional=False)
                dependencies[name] = dependency
            case Annotated(_, (Particular(InjectableDependency()), _)):
                raise AutomnConfigurationError(f"Too many arguments in type annotation for argument {name}")
            case Annotated(_, (Particular(InjectableDependency()),)):
                raise AutomnConfigurationError(f"Type annotation for argument `{name}` "
                                           "contains a marker of injectable argument, but "
                                           "Autumn component cannot be created for type "
                                           f"annotation {original_type_hint}")
    @wraps(func)
    def decorator(*args, **kwargs):
        kw: dict[str, Any] = {}
        for name, dependency in dependencies.items():
            if name in kwargs:
                continue
            if dependency.collection:
                value = dm.get_instances(dependency.interface)
                value = dependency.collection(value)
            else:
                if dependency.optional:
                    value = dm.get_instance(dependency.interface, optional=True)
                else:
                    value = dm.get_instance(dependency.interface)
            kw[name] = value
        return func(*args, **{**kwargs, **kw})
    return decorator


def session(name: str, profiles: tuple[str, ...] = ()):
    # TODO: implement resolving components by name to make 
    # Autumn look for the session by its name
    def wrapper(cls):
        if not issubclass(cls, BaseSession):
            raise AutomnConfigurationError("Session must derive BaseSession")
        cls = component(scope=SINGLETON, 
                        profiles=profiles,
                        name=name # Not implemnted
                        )(cls)
        return cls

Injectable = InjectableDependency()
Property = InjectableProperty
dm = dm
SINGLETON = SINGLETON
PROTOTYPE = PROTOTYPE