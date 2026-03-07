from typing import List, Dict, Optional, Any, IO
from model import Model
from formats.formats import AbstractFormatHandler, register_format
import json


class CocoHandler(AbstractFormatHandler):
    def read(self, file: IO) -> Optional[Model]:
        data = json.load(fp=file)
        if "images" not in data:
            raise ValueError("coco: missing 'images' entry")
        if "categories" not in data:
            raise ValueError("coco: missing 'categories' entry")
        if "annotations" not in data:
            raise ValueError("coco: missing 'categories' entry")
        model = Model()
        img_ids: Dict[int, Model.Image] = {}
        for img_data in data["images"]:
            img = Model.Image()
            img.filename = img_data["file_name"]
            img_ids[img_data["id"]] = img
            model.images.append(img)

        categories: Dict[int, str] = {}
        for category_data in data["categories"]:
            categories[category_data["id"]] = category_data["name"]

        anno_ids: Dict[int, Model.Image.Annotation] = {}
        for anno_data in data["annotations"]:
            img_id = anno_data["image_id"]
            assert img_id in img_ids
            anno = Model.Image.Annotation()
            bbox = anno_data["bbox"]
            anno.x = bbox[0]
            anno.y = bbox[1]
            anno.width = bbox[2]
            anno.height = bbox[3]
            anno.label = categories[anno_data["category_id"]]
            anno_ids[anno_data["id"]] = anno
            img_ids[img_id].annotations.append(anno)

        return model

    def write(self, model: Model, file_path: str) -> bool:
        data = self.do_write(model)
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f)
            return True
        return False

    def do_write(self, model: Model) -> Any:
        categories: Dict[str, int] = self._gen_categories(model)
        return {
            "images": self._compute_images(model),
            "annotations": self._compute_annotations(model, categories),
            "categories": self._compute_categories(categories),
        }

    def _compute_categories(self, categories: Dict[str, int]) -> List:
        ret = []
        for cat_name, cat_id in categories.items():
            ret.append({
                "id": cat_id,
                "name": cat_name,
            })
        return ret

    def _compute_image(self, image: Model.Image, img_id: int) -> dict:
        return {
            "id": img_id,
            "file_name": image.filename,
        }

    def _gen_categories(self, model: Model) -> dict:
        ret = {}
        for img in model.images:
            for anno in img.annotations:
                ret[anno.label] = len(ret)-1
        return ret

    def _compute_images(self, model: Model) -> List:
        images = []
        for img_id, img in enumerate(model.images):
            images.append(self._compute_image(img, img_id))
        return images

    def _compute_annotation(self, annotation: Model.Image.Annotation, img_id: int, anno_id: int, categories: Dict[str, int]) -> dict:
        return {
            "image_id": img_id,
            "id": anno_id,
            "bbox": [annotation.x, annotation.y, annotation.width, annotation.height],
            "category_id": categories[annotation.label],
        }

    def _compute_annotations(self, model: Model, categories: Dict[str, int]) -> List:
        annotations = []
        anno_counter = 0
        for img_id, img in enumerate(model.images):
            for anno in img.annotations:
                annotations.append(
                    self._compute_annotation(anno, img_id, anno_counter, categories))
                anno_counter += 1
        return annotations


register_format("coco", CocoHandler())
