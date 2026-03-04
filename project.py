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

        def save(self) -> dict:
            annotations = []
            for annotation in self.annotations:
                annotations.append(annotation.save())
            ret = {
                "imagefilename": self.filename,
                "annotations": annotations
            }
            return ret

    def __init__(self):
        self.json_file: str = ""
        self.folder: str = ""
        self.images: List[Project.Image] = []

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
