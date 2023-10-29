from typing import ClassVar, Protocol


class UmbrellaClient(Protocol):

    NAME: ClassVar[str] 
    
    def request(self, *args, **kwargs) -> dict:
        ...