from project.model import Model
from formats import export_to


class Project:
    def __init__(self, model: Model):
        self.default_format = "coreml"
        self.json_file: str = ""
        self.folder: str = ""
        self.model = model
        self.dirty = False

    def get_image_path(self, index: int):
        prefix = self.folder
        if len(prefix) > 0:
            prefix += "/"
        return prefix + self.model.images[index].filename

    def save_file(self):
        if export_to(self.default_format, self.model, self.json_file):
            self.dirty = False
        else:
            print("export error")
