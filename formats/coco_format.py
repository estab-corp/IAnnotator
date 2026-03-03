from project import Project
from formats.formats import AbstractFormatHandler, register_format


class CocoHandler(AbstractFormatHandler):
    def export(self, project: Project) -> dict:
        return {}


register_format("coco", CocoHandler())
