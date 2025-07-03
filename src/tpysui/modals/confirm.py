#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Confirm Modals."""

from typing import Optional

from textual import events, on
from textual.app import ComposeResult
from textual.containers import Vertical, Center, Horizontal
from textual.screen import ModalScreen
from textual.widgets import Button, Markdown, Label

EXAMPLE_MARKDOWN = """\
# New Key Created Document

You have generated a new key, copy the following information to a safe place:

_Mnemonic phrase_: '**{many word phrase}**'

_Private key_: '**{private key}**'
"""


class NewKey(ModalScreen[None]):

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

    async def _on_key(self, event: events.Key) -> None:
        if event.name == "escape":
            self.dismiss(None)

    @on(Button.Pressed, "#choice-ok")
    def on_ok(self, event: Button.Pressed) -> None:
        """
        Return the user's choice back to the calling application and dismiss the dialog
        """
        self.dismiss(None)


class OkPopup(ModalScreen[bool]):

    DEFAULT_CSS = """
        OkPopup {
            align: center middle;

            & Vertical {
                width: auto;
                height: auto;
                background: $panel;
                border: $secondary round;
            }

            & Label {
                margin: 1 2;
            }

            & Horizontal {
                width: 100%;
                height: auto;
                align: center middle;
                margin: 1 2;

                & Button {
                    width: auto;
                    margin: 0 2;
                }
            }
        }    
    """

    def __init__(self, msg: str) -> None:
        super().__init__()
        self.msg = msg

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self.msg)
            with Horizontal():
                yield Button("Ok", id="confirm", variant="primary")

    async def _on_key(self, event: events.Key) -> None:
        if event.name == "escape":
            self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(True)


class ConfirmDeleteRowDialog(ModalScreen[bool]):

    DEFAULT_CSS = """
        ConfirmDeleteRowDialog {
            align: center middle;

            & Vertical {
                width: auto;
                height: auto;
                background: $panel;
                border: $secondary round;
            }

            & Label {
                margin: 1 2;
            }

            & Horizontal {
                width: 100%;
                height: auto;
                align: center middle;
                margin: 1 2;

                & Button {
                    width: auto;
                    margin: 0 2;
                }
            }
        }    
    """

    def __init__(self, msg: str) -> None:
        super().__init__()
        self.msg = msg

    def compose(self) -> ComposeResult:
        with Vertical():
            yield Label(self.msg)
            with Horizontal():
                yield Button("Delete", id="delete", variant="error")
                yield Button("Cancel", id="cancel", variant="primary")

    async def _on_key(self, event: events.Key) -> None:
        if event.name == "escape":
            self.dismiss(False)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "delete":
            self.dismiss(True)
        else:
            self.dismiss(False)
