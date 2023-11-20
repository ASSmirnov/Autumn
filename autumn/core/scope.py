from abc import ABC, abstractmethod
from typing import Any, Mapping
from autumn.exceptions import AutomnConfigurationError, AutomnPropertyNotSet
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from autumn.core.register import Component, Register


class _DraftStorage:

    def __init__(self):
        self._cache: dict[str, Any] = {}

    def __enter__(self) -> None:
        self._cache = {}

    def __exit__(self, type, value, traceback) -> None:
        self._cache = {}

    def get(self, component_id: str) -> Any | None:
        return self._cache.get(component_id)
    
    def set(self, component_id: str, draft: Any) -> None:
        self._cache[component_id] = draft

draft_storage = _DraftStorage()


SINGLETON = "singleton"
PROTOTYPE = "prototype"

class BaseCustomScope(ABC):
    
    @abstractmethod 
    def get_instance(self) -> Any:
        ...

class _SingletonScope:

    def __init__(self):
        self._cache: dict[str, Any] = {}

    def get_instance(self, 
                     register: "Register", 
                     component: "Component", 
                     properties: Mapping[str, Any]) -> Any:
        if component.id in self._cache:
            return self._cache[component.id]
        instance = _create_instance(register, component, properties)
        self._cache[component.id] = instance
        return instance
    
    def clear_cache(self) -> None:
        self._cache = {}

class _PrototypeScope:
    
    def get_instance(self, 
                     register: "Register", 
                     component: "Component", 
                     properties: Mapping[str, Any]) -> Any:
        return _create_instance(register, component, properties)


_singleton_scope = _SingletonScope()
_prototype_scope = _PrototypeScope()


def _get_scope(component: "Component", 
               register: "Register",
               properties: Mapping[str, Any]) -> _SingletonScope | _PrototypeScope:
    if component.scope == SINGLETON:
        return _singleton_scope
    elif component.scope == PROTOTYPE:
        return _prototype_scope
    else:
        raise AutomnConfigurationError(f"Custom scopes are not supported, {component.scope}") 

def _resolve_dependency(register: "Register",
                        component: "Component", 
                        properties: Mapping[str, Any]) -> Any:

    draft_instance = draft_storage.get(component.id)
    if draft_instance is None:
        scope = _get_scope(component, register, properties)
        if scope in (_singleton_scope, _prototype_scope):
            instance = scope.get_instance(register, component, properties)
        else:
            instance = scope.get_instance()
    else:
        instance = draft_instance
    return instance

def _create_instance(register: "Register",
                     component: "Component", 
                     properties: Mapping[str, Any]) -> Any:
    fields = {}

    for name, property in component.properties.items():
        if property.name in properties:
            fields[name] = properties[property.name]
        elif property.optional:
            fields[name] = None
        else:
            raise AutomnPropertyNotSet(f"Component {component.cls} cannot be built, "
                                        f"property `{property.name}` wasn't configured")
    
    
    for name, dependency in component.dependencies.items():
        fields[name] = None

    instance = component.cls(**fields) 
    draft_storage.set(component.id, instance)
    
    for name, dependency in component.dependencies.items():
        if dependency.collection is None:
            dependency_component = register.get_compnonent(dependency.interface)
            dependency_instance = _resolve_dependency(register, dependency_component, properties)
            object.__setattr__(instance, name, dependency_instance)
        else:
            dependency_components = register.get_compnonents(dependency.interface)
            dependency_instances = []
            for dependency_component in dependency_components:
                dependency_instance = _resolve_dependency(register, dependency_component, properties)
                dependency_instances.append(dependency_instance)
            collection = dependency.collection(dependency_instances) 
            object.__setattr__(instance, name, collection)
    
    return instance

def get_instance(register: "Register",
                component: "Component", 
                properties: Mapping[str, Any]) -> Any:
    with draft_storage:
        scope = _get_scope(component, register, properties)
        if scope in (_singleton_scope, _prototype_scope):
            instance = scope.get_instance(register, component, properties)
        else:
            instance = scope.get_instance()
        return instance
    
def clear_caches():
    _singleton_scope.clear_cache()