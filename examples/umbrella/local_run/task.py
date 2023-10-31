from typing import Annotated, Any
from autumn.core.scope import SINGLETON
from autumn.public import component, Property
from examples.umbrella.dtos import Sheep, TaskDefinition
from examples.umbrella.interfaces import TaskProvider


@component(TaskProvider, scope=SINGLETON, profiles=("prod", "local"))
class LocalTaskProvider(TaskProvider):
    local_run_task: Annotated[dict[str, Any], Property("task")]

    def get_task(self) -> TaskDefinition:
        return TaskDefinition(
            id=self.local_run_task["id"],
            sheeps=[Sheep(s["name"]) for s in self.local_run_task["sheeps"]]
        )

