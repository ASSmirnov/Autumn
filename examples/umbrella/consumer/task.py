from autumn.core.scope import SINGLETON
from autumn.public import BaseCustomScope, Injectable, autowired_method, component, scope
from typing import Annotated
from examples.umbrella.dtos import TaskDefinition

from examples.umbrella.helpers import SessionManager
from examples.umbrella.interfaces import TaskProvider


@component(scope="TaskSessionScope", profiles=("prod", "umbrella"))
class Task:
    task_definition: TaskDefinition


@scope("TaskSessionScope", profiles=("prod", "umbrella"))
class TaskSession(BaseCustomScope):
    sessionManager: Annotated[SessionManager, Injectable]

    def get_instance(self) -> Task:
        value = self.sessionManager.get_session_value("task_session")
        return Task(value)


@component(TaskProvider, scope=SINGLETON, profiles=("prod", "system"))
class UmbrellaTaskProvider(TaskProvider):

    @autowired_method
    def get_task(self, task: Annotated[Task, Injectable]) -> TaskDefinition:
        return task.task_definition
