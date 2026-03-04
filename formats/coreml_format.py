from formats.formats import AbstractFormatHandler, register_format
from project import Project
from typing import List


class CoreMLHandler(AbstractFormatHandler):
    def export(self, project: Project) -> dict:
        pass

    def read(self, data: List) -> Project:
        project = Project()
        for entry in data:
            img = Project.Image()
            img.from_data(entry)
            project.images.append(img)
        return project


register_format("coreml", CoreMLHandler())
