#

"""Confirm Modals."""

from typing import Optional
from textual.screen import ModalScreen
from textual.app import ComposeResult


class ConfirmYN(ModalScreen[bool]):

    def __init__(
        self,
        confirm_text: str,
        name: Optional[str | None] = None,
        id: Optional[str | None] = None,
        classes: Optional[str | None] = None,
    ):
        self.confirm_text = confirm_text
        super().__init__(name, id, classes)

    def compose(self) -> ComposeResult:
        pass
