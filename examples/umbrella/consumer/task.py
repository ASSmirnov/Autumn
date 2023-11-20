from autumn.core.scope import SINGLETON, PROTOTYPE
from autumn.public import Injectable, component, configuration, autowired_method
from typing import Annotated
from examples.umbrella.dtos import TaskDefinition

from examples.umbrella.helpers import SessionManager
from examples.umbrella.interfaces import TaskProvider


@configuration(profiles=("prod", "system"))
class Configuration:
    sessionManager: Annotated[SessionManager, Injectable]

    @component(interface=TaskDefinition, scope=PROTOTYPE, profiles=("prod", "system")) 
    def get_task(self) -> TaskDefinition:
        return self.sessionManager.get_session_value("task_session")


@component(TaskProvider, scope=SINGLETON, profiles=("prod", "system"))
class UmbrellaTaskProvider(TaskProvider):

    @autowired_method
    def get_task(self, task_definition: Annotated[TaskDefinition, Injectable]) -> TaskDefinition:
        return task_definition
        
