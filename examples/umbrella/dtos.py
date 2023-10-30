from dataclasses import dataclass


@dataclass
class Sheep:
    name: str

@dataclass
class Task:
    id: int
    sheeps: list[Sheep]