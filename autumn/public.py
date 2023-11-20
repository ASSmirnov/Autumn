import inspect
from dataclasses import dataclass
from functools import wraps
from typing import Any, Type, dataclass_transform
from autumn.exceptions import AutomnConfigurationError

from autumn.helpers.type_hints import Collection, Optional
from .core.register import Configuration, dependency_descrition

from .core.register import register, create_component, InjectableDependency, InjectableType
from .core.manager import dm
from .core.scope import SINGLETON, PROTOTYPE


@dataclass_transform()
def component(interface: Any | None = None,
              *, 
              scope: str, 
              profiles: tuple[str, ...] = (),
              frozen: bool = True):
    if not isinstance(profiles, (list, tuple)):
        profiles = (profiles, )
    def decorator(cls_or_method):
        if inspect.ismethod(cls_or_method):
            if interface is None:
                raise AutomnConfigurationError("Interface is not optional for components "
                                               "configured via @configuration")
            setattr(cls_or_method, "__component_args__", {"interface": interface,
                                                          "scope": scope,
                                                          "profiles": profiles})
            return cls_or_method
        elif inspect.isclass(cls_or_method):
            component = create_component(interface=interface,
                                        scope=scope,
                                        profiles=profiles,
                                        cls=cls_or_method)

            component_class = dataclass(cls_or_method,
                                        eq=False, 
                                        order=False, 
                                        match_args=False, 
                                        slots=True, 
                                        frozen=frozen)
            component.cls = component_class
            register.register_component(component)
            return component_class
        else:
            raise AutomnConfigurationError("@component decorator can be applied only to classes "
                                           "or methods belonging to @configuration classes")
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


def configuration(*,
                  profiles: tuple[str, ...] = (),
                  frozen: bool = True):
    def decorator(cls):
        configuration_component = create_component(profiles=profiles,
                                                   scope=SINGLETON,
                                                   cls=cls)
        register.register_component(configuration_component)
        for member_name, member in cls.__dict__:
            component_args = getattr(member, "__component_args__")
            if component_args:
                configured_component = create_component(interface=component_args["interface"],
                                                        scope=component_args["scope"],
                                                        profiles=component_args["profiles"],
                                                        factory=Configuration(cls=cls, method_name=member_name)
                                                        )
                register.register_component(configured_component)
        component_class = dataclass(configuration_component,
                                        eq=False, 
                                        order=False, 
                                        match_args=False, 
                                        slots=True, 
                                        frozen=frozen)
        configuration_component.cls = component_class
        register.register_component(configuration_component)

        return cls
    return decorator

Injectable = InjectableDependency(type=InjectableType.component, args=())

def _property(name: str) -> InjectableDependency:
    return InjectableDependency(type=InjectableType.property, args=(name, ))

Property = _property
dm = dm
SINGLETON = SINGLETON
PROTOTYPE = PROTOTYPE