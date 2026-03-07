from typing import Dict, Optional, Set, Any, IO
from model import Model
from abc import ABC, abstractmethod


class AbstractFormatHandler(ABC):
    @abstractmethod
    def write(self, model: Model, file_path: str) -> bool:
        assert False

    @abstractmethod
    def read(self, file: IO) -> Optional[Model]:
        assert False


_formats: Dict[str, AbstractFormatHandler] = {}


def register_format(name: str, inst: AbstractFormatHandler):
    _formats[name] = inst


def export_to(name: str, model: Model, file_path: str) -> bool:
    return _formats[name].write(model, file_path)


def import_from(name: str, file: IO) -> Optional[Model]:
    if name not in _formats:
        s = f"unknown format '{name}'"
        raise ValueError(s)
    return _formats[name].read(file)


def available_formats() -> Set[str]:
    return set(_formats.keys())
