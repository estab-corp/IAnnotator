import json
from typing import List


class Project:
    class Image:
        class Annotation:
            def __init__(self):
                self.label: str = "LABEL"
                self.width = 100
                self.height = 200
                self.x = 300
                self.y = 400

            def from_data(self, data: dict):
                self.label: str = data["label"]
                center_x = data["coordinates"]["x"]
                center_y = data["coordinates"]["y"]
                self.width = data["coordinates"]["width"]
                self.height = data["coordinates"]["height"]
                self.x = center_x - self.width/2
                self.y = center_y - self.height/2

            def save(self) -> dict:
                center_x = self.x + self.width/2
                center_y = self.y + self.height/2
                ret = {
                    "label": self.label,
                    "coordinates": {
                        "x": center_x,
                        "y": center_y,
                        "width": self.width,
                        "height": self.height,
                    }
                }
                return ret

        def __init__(self):
            self.annotations: List[Project.Image.Annotation] = []
            self.filename: str = ""

        def from_data(self, data: dict):
            self.filename: str = data["imagefilename"]
            for entry in data["annotations"]:
                annotation = Project.Image.Annotation()
                annotation.from_data(entry)
                self.annotations.append(annotation)

        def save(self) -> dict:
            annotations = []
            for annotation in self.annotations:
                annotations.append(annotation.save())
            ret = {
                "imagefilename": self.filename,
                "annotations": annotations
            }
            return ret

    def __init__(self, data: dict, folder: str, json_file: str):
        self.json_file = json_file
        self.folder = folder
        self.images: List[Project.Image] = []
        self._load(data)

    def _load(self, data: dict):
        for entry in data:
            img = Project.Image()
            img.from_data(entry)
            self.images.append(img)

    def get_image_path(self, index: int):
        return self.folder + "/" + self.images[index].filename

    def save(self) -> List:
        ret = []
        for img in self.images:
            ret.append(img.save())
        return ret

    def save_file(self):
        data = self.save()
        with open(self.json_file, "w", encoding="utf-8") as f:
            json.dump(data, f)
