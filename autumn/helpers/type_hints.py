from dataclasses import dataclass
from types import NoneType, UnionType
from typing import Any, Type, get_args, get_origin, Annotated as _Annotated


@dataclass
class Generic:
    origin: Any
    args: tuple[Any, ...]

@dataclass
class Particular:
    origin: Type

@dataclass
class Optional:
    origin: Any

@dataclass
class Annotated:
    type: Any 
    args: tuple[Any, ...]

@dataclass
class Collection:
    collection_type: Type
    item_type: Any



def extract_from_hint(type_hint: Any) -> Generic | Particular | Optional:
    origin_type = get_origin(type_hint)
    if not origin_type:
        return Particular(origin=type_hint)
    
    args = get_args(type_hint)
    
    if origin_type == UnionType:
        if len(args) == 2 and NoneType in args:
            origin = [i for i in args if i is not NoneType][0]
            return Optional(origin=extract_from_hint(origin))
    
    if origin_type == _Annotated:
        return Annotated(type=extract_from_hint(args[0]),
                         args=tuple(extract_from_hint(a) for a in args[1:]))
    
    if origin_type == list:
        return Collection(type=list, item_type=extract_from_hint(args[0]))
    if origin_type == tuple:
        if (len(args) == 2 and Ellipsis in args) or len(args) == 1:
            return Collection(collection_type=tuple, item_type=extract_from_hint(args[0]))
    
    return Generic(origin=extract_from_hint(origin_type), 
                   args=tuple(extract_from_hint(i) for i in args))
                              

