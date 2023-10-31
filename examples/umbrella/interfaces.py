from abc import ABC
from typing import Any, Protocol

from dtos import TaskDefinition


class IUmbrellaClient(Protocol):

    def request(self, *args, **kwargs) -> dict:
        ...


class IConsumer(Protocol):
    
    def poll(self) -> None:
        ...

class IExecutor(Protocol):

    def execute(self, task: TaskDefinition) -> None:
        ... 

class IClient(Protocol):

    def request(self, url: str, **kwargs) -> dict[str, Any]:
        ...

class TaskProvider(ABC):

    def get_task(self) -> TaskDefinition:
        pass