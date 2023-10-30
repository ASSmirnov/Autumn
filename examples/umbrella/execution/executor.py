from abc import ABC
from typing import Annotated
from autumn.core.scope import PROTOTYPE, SINGLETON
from autumn.public import Injectable, InjectableSession, autowired_method, component
from examples.umbrella.dtos import Task
from examples.umbrella.interfaces import IExecutor


class TaskProvider(ABC):

    def get_task(self) -> Task:
        pass


@component(TaskProvider, scope=PROTOTYPE, profiles=("prod", "umbrella"))
class UmbrellaTaskProvider(TaskProvider):

    @autowired_method
    def get_task(self, task: Annotated[Task, InjectableSession]) -> Task:
        return task

@component(IExecutor, scope=SINGLETON)
class Executor:
    task_provider: Annotated[TaskProvider, Injectable]

    def execute(self):
        task = self.task_provider.get_task()
        print(f"Task executed {task}")