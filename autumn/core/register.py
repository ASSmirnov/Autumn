from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable, Mapping, Self, Type, TypeVar, overload
from uuid import uuid4
from traitlets import Any
from autumn.core.scope import can_inject_dependency, get_instance
from autumn.exceptions import AutomnComponentNotFound, AutomnConfigurationError, AutomnAmbiguousDependency
from autumn.helpers.type_hints import extract_from_hint, Annotated, Collection, Optional, Particular


@dataclass
class _Dependency:
    interface: Any
    collection: Type | None = None
    optional: bool = False


@dataclass
class _Property:
    name: str
    optional: bool



class InjectableType(Enum):
    property = "p"
    component = "c"


@dataclass
class InjectableDependency:
    type: InjectableType
    args: tuple[Any]


@dataclass
class Component:
    id: str
    scope: str
    cls: Type
    interface: Any | None
    profiles: tuple[str] = ()
    dependencies: dict[str, _Dependency] = field(default_factory=dict)
    properties: dict[str, _Property] = field(default_factory=dict)


def dependency_descrition(original_type_hint: Any) -> (Any, Any):
    type_hint = extract_from_hint(original_type_hint) 
    match type_hint:
        case Annotated(Optional(Particular(a)), (Particular(b),)):
            return (Optional(a), b)
        case Annotated(Collection(ct, Particular(a)), (Particular(b),)):
            return (Collection(ct, a), b)
        case Annotated(Particular(a), (Particular(b),)):
            return (a, b)
        case Annotated(a, (Particular(b),)):
            match b:
                case InjectableDependency(InjectableType.property):
                    return (a, b)
                case _:
                    raise AutomnConfigurationError(f"Type annotation contains a marker of injectable "
                                           "field, but Autumn cannot creat for type "
                                           f"annotation {original_type_hint}")
        case Annotated(_, (*a,)):
            for i in a:
                match i:
                    case Particular(InjectableDependency()):
                        raise AutomnConfigurationError(f"Too many arguments in type annotation.")
    return type_hint
        # case _:
        #     raise AutomnConfigurationError(f"Type annotation contains a marker of injectable "
        #                             "field, but Autumn cannot create component for type "
        #                             f"annotation {original_type_hint}")

def create_component(
    *,
    interface: Any | None,
    profiles: tuple[str, ...] = (),
    scope: str,
    cls: Type) -> Component:
    dependencies = {}
    properties = {}
    for name, original_type_hint in cls.__annotations__.items():
        type_hint = dependency_descrition(original_type_hint)
        match type_hint:
            case (Optional(t), InjectableDependency(InjectableType.component)):
                dependency = _Dependency(interface=t,
                                        collection=None,
                                        optional=True)
                dependencies[name] = dependency
            case (t, InjectableDependency(InjectableType.component)):
                dependency = _Dependency(interface=t,
                                        collection=None,
                                        optional=False)
                dependencies[name] = dependency
            case (Collection(ct, t), InjectableDependency(InjectableType.component)):
                dependency = _Dependency(interface=t,
                                        collection=ct,
                                        optional=False)
                dependencies[name] = dependency
            case (Optional(), InjectableDependency(InjectableType.property, (n,))):
                property = _Property(name=n, optional=True)
                properties[name] = property
            case (_, InjectableDependency(InjectableType.property, (n,))):
                property = _Property(name=n, optional=False)
                properties[name] = property
    
    return Component(id=str(uuid4()),
                     scope=scope,
                     cls=cls, 
                     interface=interface,
                     profiles=profiles,
                     dependencies=dependencies,
                     properties=properties) 


_T = TypeVar("_T")

class Register:
    def __init__(self) -> None:
        self._components: dict[Any, list[Component]] = {}

    def register_component(self, component: Component) -> None:
        key = component.interface if component.interface else component.cls
        self._components.setdefault(key, []).append(component)

    def check(self, properties: Iterable[str]) -> None:
        properties = set(properties)
        for _, components in self._components.items():
            for component in components:
                for field_name, dependency in component.dependencies.items():
                    if dependency.interface not in self._components:
                        if not dependency.optional:
                            raise AutomnConfigurationError("Unsatisfied dependency found for "
                            f"component {component.cls} for field `{field_name}` but the "
                            "dependency is not optional")
                        else:
                            continue
                    registered_dependencies = self._components[dependency.interface]
                    if len(registered_dependencies) > 1 and dependency.collection is None:
                        raise AutomnConfigurationError("Ambiguous dependencies found "
                            f"for component {component.cls} for field `{field_name}`, "
                            "more than one candidates found but the dependency is not a collection")
                    for registered_dependecy in registered_dependencies:
                        if not can_inject_dependency(component, registered_dependecy):
                            raise AutomnConfigurationError("Scope of component is shorter "
                                f"that scope of dependency, component: {component.cls}, "
                                f"dependency: {registered_dependecy.cls}")
                for property_name, property in component.properties.items():
                    if property_name not in properties:
                        if not property.optional:
                            raise AutomnConfigurationError("Unsatisfied dependency found for "
                            f"component {component.cls} for field `{property_name}`, "
                             "property value was not provided but the dependency is not optional")
    
    def get_instances(self, interface: _T, properties: Mapping[str, Any]) -> list[_T]:
        components = self.get_compnonents(interface)
        return [self.get_instance(self, component, properties) for component in components]
    
    @overload
    def get_instance(self, interface: _T,
                    properties: Mapping[str, Any]) -> _T:
        ...
    
    @overload
    def get_instance(self, interface: _T,
                     properties: Mapping[str, Any],
                     optional: bool) -> _T | None:
        ...

    def get_instance(self, interface: _T,
                     properties: Mapping[str, Any],
                     optional: bool = False):
        try:
            component = self.get_compnonent(interface)
        except AutomnComponentNotFound:
            if optional:
                return None
            raise
        return get_instance(self, component, properties)
    

    def get_compnonent(self, interface: Any) -> Component:
        components = self._components.get(interface)
        if components is None:
            raise AutomnComponentNotFound(f"No registered component for interface {interface}")
        if len(components) > 1:
            raise AutomnAmbiguousDependency(f"More than one component registered for interface {interface}")
        return components[0]

    def get_compnonents(self, interface: Any) -> list[Component]:
        components = self._components.get(interface)[:]
        return components



def create_register_instance(profiles: Iterable[str], properties: Iterable[str]) -> Register:
    profiles = set(profiles)
    register_instance = Register()
    global register
    for _, components in register._components.items():
        for component in components:
            for profile in component.profiles:
                if profile not in profiles:
                    break
            else:
                register_instance.register_component(component)
    register_instance.check(properties)
    return register_instance


register = Register()