from typing import Annotated
from autumn.core.scope import SINGLETON
from autumn.public import Injectable, component
from examples.umbrella.interfaces import IExecutor, TaskProvider


@component(IExecutor, scope=SINGLETON)
class Executor:
    task_provider: Annotated[TaskProvider, Injectable]

    def execute(self):
        task = self.task_provider.get_task()
        print(f"Task executed {task}")