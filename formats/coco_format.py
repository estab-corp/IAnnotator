from project import Project
from formats.formats import AbstractFormatHandler, register_format
from typing import List, Dict


class CocoHandler(AbstractFormatHandler):
    def write(self, project: Project) -> dict:
        categories: Dict[str, int] = self._gen_categories(project)
        return {
            "images": self._compute_images(project),
            "annotations": self._compute_annotations(project, categories),
            "categories": self._compute_categories(categories),
        }

    def _compute_categories(self, categories: Dict[str, int]) -> List:
        ret = []
        for cat_id, cat_name in categories.items():
            ret.append({
                "id": cat_id,
                "name": cat_name,
            })
        return ret

    def _compute_image(self, image: Project.Image, img_id: int) -> dict:
        return {
            "id": img_id,
            "file_name": image.filename,
        }

    def _gen_categories(self, project: Project) -> dict:
        ret = {}
        for img in project.images:
            for anno in img.annotations:
                ret[anno.label] = len(ret)-1
        return ret

    def _compute_images(self, project: Project) -> List:
        images = []
        for img_id, img in enumerate(project.images):
            images.append(self._compute_image(img, img_id))
        return images

    def _compute_annotation(self, annotation: Project.Image.Annotation, img_id: int, anno_id: int, categories: Dict[str, int]) -> dict:
        return {
            "image_id": img_id,
            "id": anno_id,
            "bbox": [annotation.x, annotation.y, annotation.width, annotation.height],
            "category_id": categories[annotation.label],
        }

    def _compute_annotations(self, project: Project, categories: Dict[str, int]) -> List:
        annotations = []
        anno_counter = 0
        for img_id, img in enumerate(project.images):
            for anno in img.annotations:
                annotations.append(
                    self._compute_annotation(anno, img_id, anno_counter, categories))
                anno_counter += 1
        return annotations


register_format("coco", CocoHandler())
