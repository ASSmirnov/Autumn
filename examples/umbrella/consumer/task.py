from autumn.public import BaseScope, Injectable, scope
from typing import Annotated
from examples.umbrella.dtos import Task

from examples.umbrella.helpers import SessionManager



@scope(Task, profiles=("prod", "umbrella"))
class TaskSession(BaseScope):
    sessionManager: Annotated[SessionManager, Injectable]

    def get_instance(self):
        value = self.sessionManager.get_session_value("task_session")
        return value
