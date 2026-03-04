from typing import Dict, Optional, Set
from model import Model


class AbstractFormatHandler:
    def write(self, model: Model) -> any:
        assert False

    def read(self, data: any) -> Optional[Model]:
        assert False


_formats: Dict[str, AbstractFormatHandler] = {}


def register_format(name: str, inst: AbstractFormatHandler):
    _formats[name] = inst


def export_to(name: str, model: Model) -> dict:
    return _formats[name].write(model)


def import_from(name: str, data: any) -> Optional[Model]:
    if name not in _formats:
        s = f"unknown format '{name}'"
        raise ValueError(s)
    return _formats[name].read(data)


def available_formats() -> Set[str]:
    return _formats.keys()
