from dataclasses import dataclass


@dataclass
class Sheep:
    name: str

@dataclass
class TaskDefinition:
    id: int
    sheeps: list[Sheep]