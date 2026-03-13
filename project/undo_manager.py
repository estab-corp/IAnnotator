from typing import List, Optional
from project.model import Model
from annotator.inspector_interface import ChangeReason, ChangeDiff


class UndoManager:
    class Command:
        def __init__(self, reason: ChangeReason, img_index: int, anno_index: int, diff: Optional[ChangeDiff] = None):
            self.reason = reason
            self.img_index = img_index
            self.anno_index = anno_index
            self.diff: Optional[ChangeDiff] = diff

        def __str__(self) -> str:
            return f"img={self.img_index} anno={self.anno_index} reason={self.reason.name} diff={self.diff}"

    def __init__(self):
        self.commands: List[UndoManager.Command] = []
        self.head: int = 0

    def push_change(self, change: Command):
        last_len = len(self.commands)
        if self.head != last_len:
            # A change is pushed after 'undo' was used. Need to clear the commands *after*.
            self.commands = self.commands[0:self.head]
        self.commands.append(change)
        self.head = len(self.commands)

    def num_prev_commands(self) -> int:
        return self.head

    def undo(self, model: Model):
        cmd: UndoManager.Command = self.commands[self.head-1]
        self._undo_cmd(model, cmd)
        self.head -= 1

    def _undo_cmd(self, model: Model, cmd: Command):
        if cmd.reason == ChangeReason.ANNO_ADDED:
            del model.images[cmd.img_index].annotations[cmd.anno_index]
        elif cmd.reason == ChangeReason.ANNO_DELETED:
            assert cmd.diff
            assert cmd.diff.annotation
            model.images[cmd.img_index].annotations.insert(
                cmd.anno_index, cmd.diff.annotation)
        elif cmd.reason == ChangeReason.LABEL:
            assert cmd.diff
            assert cmd.diff.label
            model.images[cmd.img_index].annotations[cmd.anno_index].label = cmd.diff.label
        elif cmd.reason == ChangeReason.ANNO_GEOMETRY:
            assert cmd.diff
            if cmd.diff.x:
                model.images[cmd.img_index].annotations[cmd.anno_index].x -= cmd.diff.x
            if cmd.diff.y:
                model.images[cmd.img_index].annotations[cmd.anno_index].y -= cmd.diff.y
            if cmd.diff.w:
                model.images[cmd.img_index].annotations[cmd.anno_index].width -= cmd.diff.w
            if cmd.diff.h:
                model.images[cmd.img_index].annotations[cmd.anno_index].height -= cmd.diff.h
        else:
            print(f"unhandled undo reason {cmd}")
            assert 0

    def redo(self, model: Model):
        if len(self.commands) == 0 or self.head == len(self.commands):
            return
        cmd: UndoManager.Command = self.commands[self.head]
        self._redo_cmd(model, cmd)
        self.head += 1

    def _redo_cmd(self, model: Model, cmd: Command):
        if cmd.reason == ChangeReason.ANNO_GEOMETRY:
            assert cmd.diff
            if cmd.diff.x:
                model.images[cmd.img_index].annotations[cmd.anno_index].x += cmd.diff.x
            if cmd.diff.y:
                model.images[cmd.img_index].annotations[cmd.anno_index].y += cmd.diff.y
            if cmd.diff.w:
                model.images[cmd.img_index].annotations[cmd.anno_index].width += cmd.diff.w
            if cmd.diff.h:
                model.images[cmd.img_index].annotations[cmd.anno_index].height += cmd.diff.h
        else:
            print(f"unhandled undo reason {cmd}")
            assert 0
