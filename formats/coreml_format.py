from formats.formats import AbstractFormatHandler, register_format
from typing import List
from model import Model


class CoreMLHandler(AbstractFormatHandler):
    def export(self, model: Model) -> dict:
        pass

    def read(self, data: List) -> Model:
        model = Model()
        for entry in data:
            img = self._image_from_data(entry)
            model.images.append(img)
        return model

    def _annotation_from_data(self, data: dict) -> Model.Image.Annotation:
        anno = Model.Image.Annotation()
        anno.label = data["label"]
        center_x = data["coordinates"]["x"]
        center_y = data["coordinates"]["y"]
        anno.width = data["coordinates"]["width"]
        anno.height = data["coordinates"]["height"]
        anno.x = center_x - anno.width/2
        anno.y = center_y - anno.height/2
        return anno

    def _image_from_data(self, data: dict) -> Model.Image:
        img = Model.Image()
        img.filename = data["imagefilename"]
        for entry in data["annotations"]:
            annotation = self._annotation_from_data(entry)
            img.annotations.append(annotation)
        return img


register_format("coreml", CoreMLHandler())
