
from typing import ClassVar
from autumn.public import component, SINGLETON
from client.types import UmbrellaClient


@component(interface=UmbrellaClient, scope=SINGLETON, profiles=("prod", "system"))
class SystemClient:
    NAME: ClassVar[str] = "@@SystemClient@@"

    def request(self) -> dict:

        return {"payload": None, 
                "say": "OK",
                "credentials": None}