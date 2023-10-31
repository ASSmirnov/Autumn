from typing import Annotated
from autumn.core.scope import SINGLETON
from autumn.public import Injectable, component
from examples.umbrella.interfaces import IExecutor, TaskProvider
from collections import Counter

@component(IExecutor, scope=SINGLETON)
class Executor:
    task_provider: Annotated[TaskProvider, Injectable]

    def execute(self) -> dict[str, int]:
        task = self.task_provider.get_task()
        counter = Counter([s.name for s in task.sheeps])
        print(f"Task id={task.id} executed, sheeps: ")
        for sheep in task.sheeps:
            count = counter[sheep.name]
            print(f"Name: {sheep.name}, count: {count}")
        return dict(counter)