from project.model import Model
from project.undo_manager import UndoManager, ChangeDiff, ChangeReason
from formats import export_to
from abc import ABC, abstractmethod
from typing import List, Optional
import os


class ProjectWatcher(ABC):
    @abstractmethod
    def annotation_list_changed(self, img_index: int):
        pass


class Project:
    @staticmethod
    def new_default():
        p = Project(Model())
        p.default_format = "coco"
        return p

    def __init__(self, model: Model):
        self.default_format = "coreml"
        self.json_file: str = ""
        self.model = model
        self.dirty = False
        self.undo_manager = UndoManager()
        self.watchers: List[ProjectWatcher] = []

    def get_folder(self) -> str:
        print(f"self.json_file='{self.json_file}'")
        if self.json_file != "":
            ret = os.path.dirname(os.path.abspath(self.json_file))
            print(f"dirname:'{self.json_file}'")
            return ret
        return os.getcwd()

    def _notify_annotation_list_changed(self, img_index: int):
        for w in self.watchers:
            w.annotation_list_changed(img_index)

    def get_image_path(self, index: int):
        ret = self.get_folder() + "/" + self.model.images[index].filename
        print(ret)
        return ret

    def save_file(self):
        if export_to(self.default_format, self.model, self.json_file):
            self.dirty = False
        else:
            print("export error")

    def save_as_file(self, filepath: str, format_: str):
        if export_to(format_, self.model, filepath):
            self.dirty = False
            self.default_format = format_
            self.json_file = filepath
        else:
            print("export error")

    def _commit(self, reason: ChangeReason, img_idx: int, anno_idx: int, diff: Optional[ChangeDiff]):
        was_clean = self.dirty is False
        self.dirty = True
        self.undo_manager.push_change(UndoManager.Command(
            reason=reason,
            img_index=img_idx,
            anno_index=anno_idx,
            diff=diff), mark_dirty=was_clean)

    def remove_annotation(self, img_idx: int, anno_idx: int):
        delete_anno = self.model.images[img_idx].annotations[anno_idx]
        del self.model.images[img_idx].annotations[anno_idx]

        diff = ChangeDiff()
        diff.annotation = delete_anno

        self._commit(reason=ChangeReason.ANNO_DELETED,
                     img_idx=img_idx, anno_idx=anno_idx, diff=None)
        self._notify_annotation_list_changed(img_idx)

    def add_annotation(self, img_idx: int, annotation: Model.Image.Annotation):
        image = self.model.images[img_idx]
        image.annotations.append(annotation)

        new_anno_index = len(image.annotations)-1
        diff = ChangeDiff()
        diff.annotation = annotation
        self._commit(reason=ChangeReason.ANNO_ADDED,
                     img_idx=img_idx, anno_idx=new_anno_index, diff=diff)
        self._notify_annotation_list_changed(img_idx)

    def duplicate_annotation(self, img_idx: int, anno_idx: int):
        image = self.model.images[img_idx]
        image_copy = image.annotations[anno_idx].copy()
        image_copy.x += 30
        image_copy.y += 30
        self.add_annotation(img_idx, image_copy)

    def update_annotation(self, img_idx: int, anno_idx: int, reason: ChangeReason, diff: Optional[ChangeDiff]):
        self._commit(reason=reason, img_idx=img_idx,
                     anno_idx=anno_idx, diff=diff)
        self._notify_annotation_list_changed(img_idx)
