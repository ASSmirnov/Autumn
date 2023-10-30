from typing import Any
from autumn.core.scope import SINGLETON
from autumn.public import component
from examples.umbrella.interfaces import IClient

current = 0

@component(IClient, scope=SINGLETON, profiles=("prod", "system"))
class Client:

    def request(self, url: str, **kwargs) -> dict[str, Any]:
        print(f"Requesting {url}")
        global current
        current += 1
        return {
            "payload": {"id": current, "sheeps": [{"name": "Dolly"}, {"name": "Sveta"}]}
        }