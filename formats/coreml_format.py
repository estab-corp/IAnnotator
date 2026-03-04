from formats.formats import AbstractFormatHandler, register_format
from project import Project


class CoreMLHandler(AbstractFormatHandler):
    def export(self, project: Project) -> dict:
        pass

    def read(self, data: any) -> Project:
        assert (False)


register_format("coreml", CoreMLHandler())
