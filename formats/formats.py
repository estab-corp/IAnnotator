from project import Project
from typing import Dict


class AbstractFormatHandler:
    def export(self, project: Project) -> dict:
        assert (False)


_formats: Dict[str, AbstractFormatHandler] = {}


def register_format(name: str, inst: AbstractFormatHandler):
    _formats[name] = inst


def export_to(name: str, project: Project) -> dict:
    return _formats[name].export(project)
