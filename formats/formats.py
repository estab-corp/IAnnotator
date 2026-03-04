from model import Model
from typing import Dict, Optional, Set


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
    return _formats[name].read(data)


def available_formats() -> Set[str]:
    return _formats.keys()
