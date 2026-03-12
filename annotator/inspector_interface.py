from typing import Tuple, Optional
from enum import IntEnum
from project.model import Model


class ChangeReason(IntEnum):
    ANNO_GEOMETRY = 0
    ANNO_DELETED = 1
    ANNO_ADDED = 2
    LABEL = 3


class ChangeDiff:
    def __init__(self):
        self.x: Optional[int] = None
        self.y: Optional[int] = None
        self.w: Optional[int] = None
        self.h: Optional[int] = None
        self.label: Optional[str] = None
        # set when reason is Delete
        self.annotation: Optional[Model.Image.Annotation] = None

    def __repr__(self) -> str:
        return f"dx={self.x} dy={self.y} dw={self.w} dh={self.h} label={self.label}"


class InspectorInterface:
    def annotations_selection_changed(self, index):
        pass

    def annotations_changed(self, index,  reason: ChangeReason, commit: bool = True, diff: Optional[ChangeDiff] = None):
        pass

    def mouse_pos_changed(self, coords: Tuple[int, int]):
        pass
