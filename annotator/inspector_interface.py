from typing import Tuple, Optional
from project.undo_manager import ChangeReason, ChangeDiff


class InspectorInterface:
    def annotations_selection_changed(self, index):
        pass

    def annotations_changed(self, index,  reason: ChangeReason, commit: bool = True, diff: Optional[ChangeDiff] = None):
        pass

    def mouse_pos_changed(self, coords: Tuple[int, int]):
        pass
