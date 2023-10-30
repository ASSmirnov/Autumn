from typing import Any, Protocol

from dtos import Task


class IUmbrellaClient(Protocol):

    def request(self, *args, **kwargs) -> dict:
        ...


class IConsumer(Protocol):
    
    def poll(self) -> None:
        ...

class IExecutor(Protocol):

    def execute(self, task: Task) -> None:
        ... 

class IClient(Protocol):

    def request(self, url: str, **kwargs) -> dict[str, Any]:
        ...