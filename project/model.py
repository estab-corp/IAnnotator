from typing import List, Set
import copy


class Model:
    class Image:
        class Annotation:
            def __init__(self):
                self.label: str = ""
                self.width: int = 0
                self.height: int = 0
                self.x: int = 0
                self.y: int = 0

            def copy(self) -> 'Model.Image.Annotation':
                return copy.deepcopy(self)

        def __init__(self):
            self.annotations: List[Model.Image.Annotation] = []
            self.filename: str = ""
            self.loaded_width = 0
            self.loaded_height = 0

    def __init__(self):
        self.images: List[Model.Image] = []

    def get_classes(self) -> Set[str]:
        classes: Set[str] = set()
        for img in self.images:
            for anno in img.annotations:
                classes.add(anno.label)
        return classes

    def get_num_annotations(self) -> int:
        count = 0
        for img in self.images:
            count += len(img.annotations)
        return count
