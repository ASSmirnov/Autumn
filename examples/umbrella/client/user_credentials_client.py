from typing import Annotated, ClassVar
from autumn.public import Property, Injectable, autowired_method, component, SINGLETON, PROTOTYPE, dm

from .types import UmbrellaClient

@component(scope=SINGLETON, profiles=("prod", "local"))
class TogglesProvider:
    client: Annotated[UmbrellaClient, Injectable]

    def get_toggles(self) -> list[str]:
        return [f"Toggle1_{self.client.NAME}", "Toggle2"]


@component(scope=PROTOTYPE)
class Volatile:
    
    toggles_provider: Annotated[TogglesProvider | None, Injectable]
    
    def say(self) -> None:
        return f"Ok, {self.toggles_provider.client.NAME}"

@component(interface=UmbrellaClient, scope=SINGLETON, profiles=("prod", "local"))
class UserCredentialClient:
    NAME: ClassVar[str] = "@@UserCredentialClient@@"
    credentials: Annotated[str, Property("credentials")]
    toggles_provider: Annotated[TogglesProvider, Injectable]

    def request(self) -> dict:
        volatile = dm.get_instance(Volatile)
        self.method_injected(a=100)
        return {"payload": self.toggles_provider.get_toggles(), 
                "say": volatile.say(),
                "credentials": self.credentials}

    @autowired_method
    def method_injected(self, i: Annotated[Volatile, Injectable], a: int) -> None:
        print("autowired method call", i.say(), a)