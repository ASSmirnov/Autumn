from dataclasses import dataclass, field
from enum import Enum
import inspect
from typing import Iterable, Mapping, Type, TypeVar, overload, Any
from uuid import uuid4
from autumn.core.scope import PROTOTYPE, SESSION, SINGLETON, BaseCustomScope, get_instance
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
    session_object = "s"


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
                        raise AutomnConfigurationError(
                            f"Too many arguments in type annotation.")
    return type_hint


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
            case (_, InjectableDependency(InjectableType.session_object)):
                raise AutomnConfigurationError("InjectabjeSession is not applicable on "
                                               "component definition level. You may use "
                                               "injection with `autowared_method`")

    return Component(id=str(uuid4()),
                     scope=scope,
                     cls=cls,
                     interface=interface,
                     profiles=profiles,
                     dependencies=dependencies,
                     properties=properties)


_T = TypeVar("_T")


_registered_components: set[str] = set()


class Register:
    def __init__(self) -> None:
        self._components: dict[Any, list[Component]] = {}
        self._scopes: dict[Any, list[Component]] = {}

    def _get_id(self, interface: Type) -> int:
        file = inspect.getfile(interface)
        return f"{file}:{interface.__name__}"

    def register_component(self, component: Component) -> None:
        # Class can be imported more then once, we should not
        # register them few times
        component_id = self._get_id(component.cls)
        global _registered_components
        if component_id in _registered_components:
            return
        _registered_components.add(component_id)

        if component.scope == SESSION:
            component.scope = SINGLETON
            key = component.interface
            self._scopes.setdefault(key, []).append(component)
        else:
            interface = component.interface or component.cls
            key = self._get_id(interface)
            self._components.setdefault(key, []).append(component)

    def check(self, properties: Iterable[str]) -> None:
        properties = set(properties)
        for _, components in self._components.items():
            for component in components:
                for field_name, dependency in component.dependencies.items():
                    registered_dependencies = self.get_compnonents(
                        dependency.interface)
                    if not registered_dependencies:
                        if not dependency.optional:
                            raise AutomnComponentNotFound("Unsatisfied dependency found for "
                                                          f"component {component.cls} for field `{field_name}` but the "
                                                          "dependency is not optional")
                        else:
                            continue
                    for registered_dependency in registered_dependencies:
                        if registered_dependency.scope not in (SINGLETON, PROTOTYPE):
                            raise AutomnConfigurationError("Custom scope dependencies are not "
                                                           "permitted as class dependencies, always "
                                                           "inject them via methonds")
                    if len(registered_dependencies) > 1 and dependency.collection is None:
                        raise AutomnAmbiguousDependency("Ambiguous dependencies found "
                                                        f"for component {component.cls} for field `{field_name}`, "
                                                        "more than one candidates found but the dependency is not a collection")
                for property_name, property in component.properties.items():
                    if property_name not in properties:
                        if not property.optional:
                            raise AutomnComponentNotFound("Unsatisfied dependency found for "
                                                          f"component {component.cls} for field `{property_name}`, "
                                                          "property value was not provided but the dependency is not optional")
        for _, components in self._scopes.items():
            if len(components) > 1:
                raise AutomnAmbiguousDependency(
                    f"More than one scope found for name {components[0].interface}")

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

    def get_scope(self, name: str, properties: Mapping[str, Any]) -> BaseCustomScope:
        scopes = self._scopes.get(name)
        if scopes is None:
            print(self._scopes)
            raise AutomnComponentNotFound(f"Scope `{name}` not found")
        scope_component = scopes[0]
        scope_instance = get_instance(self, scope_component, properties)
        return scope_instance

    def get_compnonent(self, interface: Any) -> Component:
        components = self.get_compnonents(interface)
        if not components:
            raise AutomnComponentNotFound(
                f"No registered component for interface {interface}")
        if len(components) > 1:
            raise AutomnAmbiguousDependency(
                f"More than one component registered for interface {interface}")
        return components[0]

    def get_compnonents(self, interface: Any) -> list[Component]:
        key = self._get_id(interface)
        components = self._components.get(key, [])[:]
        return components


def create_register_instance(profiles: Iterable[str], properties: Iterable[str]) -> Register:
    profiles = set(profiles)
    register_instance = Register()

    def filter_components(components_dict):
        result_dict = {}
        for t, components in components_dict.items():
            for component in components:
                for profile in component.profiles:
                    if profile not in profiles:
                        break
                else:
                    result_dict.setdefault(t, []).append(component)
        return result_dict
    register_instance._components = filter_components(register._components)
    register_instance._scopes = filter_components(register._scopes)
    register_instance.check(properties)
    return register_instance


register = Register()
