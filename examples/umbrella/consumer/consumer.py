from typing import Annotated
from autumn.core.scope import SINGLETON
from autumn.public import Injectable, component
from examples.umbrella.dtos import TaskDefinition, Sheep
from examples.umbrella.helpers import SessionManager
from examples.umbrella.interfaces import IClient, IConsumer, IExecutor


@component(IConsumer, scope=SINGLETON, profiles=("prod", "umbrella"))
class Consumer:
    session_manager: Annotated[SessionManager, Injectable]
    client: Annotated[IClient, Injectable]
    executor: Annotated[IExecutor, Injectable]

    def poll(self) -> None:
       for _ in range(3):
        raw_task = self.client.request("http://pentagon/get_task")
        sheeps = [Sheep(s["name"]) for s in raw_task["payload"]["sheeps"]]
        task = TaskDefinition(id=raw_task["payload"]["id"], sheeps=sheeps)
        with self.session_manager.activate("task_session", task):
            self.executor.execute()