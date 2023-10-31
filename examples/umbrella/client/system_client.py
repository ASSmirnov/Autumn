from typing import Annotated, Any, ClassVar
from autumn.core.scope import PROTOTYPE, SINGLETON
from autumn.public import Injectable, component
from examples.umbrella.interfaces import IClient

current = 0

class ISheep:
    name: str

@component(ISheep, scope=PROTOTYPE)
class Sheep1:
    name: ClassVar[str] = "Sveta"

@component(ISheep, scope=PROTOTYPE)
class Sheep:
    name: ClassVar[str] = "Marina"


@component(ISheep, scope=PROTOTYPE)
class Sheep2:
    name: ClassVar[str] = "Masha"

@component(ISheep, scope=PROTOTYPE)
class Sheep3:
    name: ClassVar[str]   = "Nina"

@component(ISheep, scope=PROTOTYPE)
class Sheep4:
    name: ClassVar[str] = "Sveta"


@component(ISheep, scope=PROTOTYPE)
class Sheep5:
    name: ClassVar[str] = "Sveta"

@component(ISheep, scope=PROTOTYPE)
class Sheep6:
    name: ClassVar[str] = "Marina"


@component(scope=SINGLETON)
class Pentagon:
    sheeps: Annotated[list[ISheep], Injectable]
    
    def get_sheeps(self) -> list[dict]:
        return [{"name": sheep.name} for sheep in self.sheeps]

@component(IClient, scope=SINGLETON, profiles=("prod", "system"))
class Client:
    pentagon: Annotated[Pentagon, Injectable]

    def request(self, url: str, **kwargs) -> dict[str, Any]:
        print(f"Requesting {url}")
        global current
        current += 1
        return {
            "payload": {"id": current, "sheeps": self.pentagon.get_sheeps()}
        }