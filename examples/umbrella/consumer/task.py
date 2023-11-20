from autumn.core.scope import SINGLETON, PROTOTYPE
from autumn.public import Injectable, autowired_method, component
from typing import Annotated
from examples.umbrella.dtos import TaskDefinition

from examples.umbrella.helpers import SessionManager
from examples.umbrella.interfaces import TaskProvider


@component(TaskProvider, scope=SINGLETON, profiles=("prod", "system"))
class UmbrellaTaskProvider(TaskProvider):
    sessionManager: Annotated[SessionManager, Injectable]

    def get_task(self) -> TaskDefinition:
        return self.sessionManager.get_session_value("task_session")
        
