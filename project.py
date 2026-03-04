import json
from typing import List
from model import Model


class Project:
    def __init__(self, model: Model):
        self.json_file: str = ""
        self.folder: str = ""
        self.model = model

    def get_image_path(self, index: int):
        return self.folder + "/" + self.model.images[index].filename

    def save(self) -> List:
        ret = []
        for img in self.model.images:
            ret.append(img.save())
        return ret

    def save_file(self):
        data = self.save()
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
