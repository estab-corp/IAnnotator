from project import Project
from formats.formats import AbstractFormatHandler, register_format
from typing import List


class CocoHandler(AbstractFormatHandler):
    def export(self, project: Project) -> dict:
        return {
            "images": self._compute_images(project),
            "annotations": self._compute_annotations(project),
        }

    def _compute_image(self, image: Project.Image, img_id: int) -> dict:
        return {
            "id": img_id,
            "file_name": image.filename,
        }

    def _compute_images(self, project: Project) -> List:
        images = []
        for img_id, img in enumerate(project.images):
            images.append(self._compute_image(img, img_id))
        return images

    def _compute_annotation(self, annotation: Project.Image.Annotation, img_id: int, anno_id: int) -> dict:
        return {
            "image_id": img_id,
            "id": anno_id,
            "bbox": [annotation.x, annotation.y, annotation.width, annotation.height]
        }

    def _compute_annotations(self, project: Project) -> List:
        annotations = []
        anno_counter = 0
        for img_id, img in enumerate(project.images):
            for anno in img.annotations:
                annotations.append(
                    self._compute_annotation(anno, img_id, anno_counter))
                anno_counter += 1
        return annotations


register_format("coco", CocoHandler())
