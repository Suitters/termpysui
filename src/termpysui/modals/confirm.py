#

"""Confirm Modals."""

from typing import Optional

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Vertical, Center
from textual.screen import ModalScreen
from textual.widgets import Button, Markdown

EXAMPLE_MARKDOWN = """\
# New Key Created Document

You have generated a new key, copy the following information to a safe place:

_Mnemonic phrase_: '**{many word phrase}**'

_Private key_: '**{private key}**'
"""


class NewKey(ModalScreen[bool]):

    DEFAULT_CSS = """
    NewKey {
        width: 50%;
        align: center top;    
        background: $primary 10%;   
        border: white; 
    }
    #confirm-key-dlg {
        width: 50%;
        height: 50%;
        border: white 80%;
        content-align: center top;
        margin: 1;
    }
    .center {
        content-align: center top;
    }
    Button {
        width: 20%;
        margin: 1;
    }
    """

    def __init__(
        self,
        mnem_phrase: str,
        priv_key: str,
        name: Optional[str | None] = None,
        id: Optional[str | None] = None,
        classes: Optional[str | None] = None,
    ):
        self.utext = EXAMPLE_MARKDOWN.replace(
            "{many word phrase}", mnem_phrase
        ).replace("{private key}", priv_key)
        # self.confirm_text = confirm_text
        super().__init__(name, id, classes)

    def compose(self) -> ComposeResult:
        yield Vertical(
            Markdown(self.utext),
            Center(Button("OK", variant="primary", id="choice-ok")),
            id="confirm-key-dlg",
        )

    def _on_key(self, event: events.Key) -> None:
        if event.name == "escape":
            self.dismiss(None)
        return super()._on_key(event)

    @on(Button.Pressed, "#choice-ok")
    def on_ok(self, event: Button.Pressed) -> None:
        """
        Return the user's choice back to the calling application and dismiss the dialog
        """
        self.dismiss(None)
