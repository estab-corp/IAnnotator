import json
from typing import List
from model import Model
from formats import export_to


class Project:
    def __init__(self, model: Model):
        self.json_file: str = ""
        self.folder: str = ""
        self.model = model

    def get_image_path(self, index: int):
        return self.folder + "/" + self.model.images[index].filename

    def save_file(self):
        data = export_to("coreml", self.model)
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
