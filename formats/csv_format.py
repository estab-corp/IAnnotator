from typing import List, Dict, Optional, IO
from model import Model
from formats.formats import AbstractFormatHandler, register_format
import csv


class CSVHandler(AbstractFormatHandler):
    def read(self, file: IO) -> Optional[Model]:
        reader = csv.reader(file)
        model = Model()
        for row in reader:
            filename, width, height, clss, xmin, ymin, xmax, ymax = row
            try:
                self._add_entry(model, filename, float(width), float(height),
                                clss, float(xmin), float(ymin), float(xmax), float(ymax))
            except ValueError as e:
                print(e)
                continue
        return model

    def _add_annotation(self, img: Model.Image, clss, xmin, ymin, xmax, ymax):
        anno = Model.Image.Annotation()
        anno.label = clss
        anno.x = xmin
        anno.y = ymin
        anno.width = xmax - xmin
        anno.height = ymax - ymin
        img.annotations.append(anno)

    def _add_entry(self, model: Model, filename, width, height, clss, xmin, ymin, xmax, ymax):
        for img in model.images:
            if img.filename == filename:
                self._add_annotation(img, clss, xmin, ymin, xmax, ymax)
                return
        img = Model.Image()
        img.filename = filename
        self._add_annotation(img, clss, xmin, ymin, xmax, ymax)
        model.images.append(img)

    def write(self, model: Model, file_path: str) -> bool:
        print("CSVHandler.write not implemented")
        assert 0
        return False


register_format("csv", CSVHandler())
