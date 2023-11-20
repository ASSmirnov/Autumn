from typing import Any
from autumn.core.scope import SINGLETON
from autumn.public import component

class _Session:
    
    def __init__(self, parent, value, name) -> None:
        self.parent = parent
        self.value = value
        self.name = name

    def __enter__(self):
        pass

    def __exit__(self, *args):
        del self.value
        self.parent.deactivate(self.name)

@component(scope=SINGLETON)
class SessionManager:
    _sessions = {}

    def session(self, name):
        return self._sessions[name] 

    def activate(self, name, value):
        session = _Session(self, value, name)
        self._sessions[name] = session
        return session
    
    def deactivate(self, name):
        del self._sessions[name]

    def get_session_value(self, name) -> Any:
        if name not in self._sessions:
            raise Exception("Session is not active.")
        return self._sessions[name].value
