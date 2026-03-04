from project import Project
from typing import Dict, Optional, Set


class AbstractFormatHandler:
    def write(self, project: Project) -> dict:
        assert (False)

    def read(self, data: any) -> Optional[Project]:
        assert (False)


_formats: Dict[str, AbstractFormatHandler] = {}


def register_format(name: str, inst: AbstractFormatHandler):
    _formats[name] = inst


def export_to(name: str, project: Project) -> dict:
    return _formats[name].write(project)


def import_from(name: str, data: any) -> Optional[Project]:
    return _formats[name].read(data)


def available_formats() -> Set[str]:
    return _formats.keys()
