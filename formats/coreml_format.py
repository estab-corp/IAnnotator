from typing import Optional, Any, IO
from formats.formats import AbstractFormatHandler, register_format
from project.model import Model
import json


class CoreMLHandler(AbstractFormatHandler):
    def write(self, model: Model, file_path: str) -> bool:
        data = self.do_write(model)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
            return True
        return False

    def do_write(self, model: Model) -> Any:
        ret = []
        for img in model.images:
            ret.append(self._write_image(img))
        return ret

    def _write_annotation(self, anno: Model.Image.Annotation) -> dict:
        center_x = anno.x + anno.width/2
        center_y = anno.y + anno.height/2
        ret = {
            "label": anno.label,
            "coordinates": {
                "x": center_x,
                "y": center_y,
                "width": anno.width,
                "height": anno.height,
            }
        }
        return ret

    def _write_image(self, image: Model.Image) -> dict:
        annotations = []
        for annotation in image.annotations:
            annotations.append(self._write_annotation(annotation))
        ret = {
            "imagefilename": image.filename,
            "annotations": annotations
        }
        return ret

    def read(self, file: IO) -> Optional[Model]:
        data = json.load(fp=file)
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
