import json
from pathlib import Path
from typing import Annotated, ClassVar

from autumn.core.scope import SINGLETON
from autumn.public import Injectable, component
from examples.umbrella.dtos import Sheep, TaskDefinition
from examples.umbrella.interfaces import TaskProvider

class Resource:
    ...

@component(Resource, scope=SINGLETON, profiles=("test_male",))
class Resource1:
    task_path: ClassVar = Path(__file__).parent.parent / "tests" / "resources" / "task_male.json"


@component(Resource, scope=SINGLETON, profiles=("test_female",))
class Resource2:
    task_path: ClassVar = Path(__file__).parent.parent / "tests" / "resources" / "task_female.json"


@component(TaskProvider, scope=SINGLETON, profiles=("test", ))
class TestTaskProvider(TaskProvider):
    resource: Annotated[Resource | None, Injectable]

    def get_task(self) -> TaskDefinition:
        assert self.resource
        with open(self.resource.task_path) as f:
            test_task = json.load(f)
        return TaskDefinition(
            id=test_task["id"],
            sheeps=[Sheep(s["name"]) for s in test_task["sheeps"]]
        )