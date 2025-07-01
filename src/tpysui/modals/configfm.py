#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Configuration file management modals."""

from pathlib import Path
from typing import Iterable
from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalGroup, HorizontalGroup
from textual.screen import ModalScreen
from textual.widgets import DirectoryTree, Input, Button, Tree


class ConfigDir(DirectoryTree):
    """."""

    def filter_paths(self, paths: Iterable[Path]) -> Iterable[Path]:
        return [path for path in paths if path.is_dir]

    def _on_click(self, event):
        if event.chain == 1:
            # single click: prevent default behavior, don't select
            event.prevent_default()
            if (line := event.style.meta.get("line", -1)) > -1:
                # but highlight the line that was clicked
                self.cursor_line = line
                self.hover_line = line


class ConfigPicker(ModalScreen[Path | None]):
    """."""

    DEFAULT_CSS = """
    ConfigPicker {
        align: center middle;        
    }
    #ConfigPopup {
        align: center middle;
        width: 80;  # Width of the modal
        height: 20; # Height of the modal
    }
    .dir_list {
        border: blue;
    }
    .center {
        content-align: center middle;
    }
    """

    def __init__(
        self, config_accept: str, name: str = None, id: str = None, classes: str = None
    ) -> None:
        super().__init__(name, id, classes)
        self.config_accept = config_accept or "PysuiConfig.json"

    def compose(self) -> ComposeResult:
        with Horizontal(id="ConfigPopup"):
            yield ConfigDir("~/", classes="dir_list")

    @on(DirectoryTree.FileSelected)
    def ft_selected(self, event: DirectoryTree.FileSelected):
        if event.path.name == self.config_accept:
            self.dismiss(event.path)

    async def _on_key(self, event: events.Key) -> None:
        if event.name == "escape":
            self.dismiss(None)
        return super()._on_key(event)


class ConfigSaver(ModalScreen[Path | None]):
    """Save to configuration."""

    DEFAULT_CSS = """
    ConfigSaver {
        align: center top;        
    }
    .save_popup {
        align: center top;
        width: 80;  # Width of the modal
        height: 40; # Height of the modal
    }
    .dir_list {
        border: blue;
    }
    .input {
        width: 70%;
        margin:1;
    }
    .button {
        width: 20%;
        margin:1;
    }
    """

    def compose(self) -> ComposeResult:
        with VerticalGroup(classes="save_popup"):
            with HorizontalGroup():
                yield Input(placeholder="~/", classes="input")
                yield Button(
                    "Save To",
                    variant="primary",
                    classes="button",
                    id="single-choice-ok",
                )
            yield ConfigDir("~/", classes="dir_list")
        # return super().compose()

    async def _on_key(self, event: events.Key) -> None:
        if event.name == "escape":
            self.dismiss(None)
        return super()._on_key(event)

    @on(Tree.NodeHighlighted)
    def ft_selected(self, event: Tree.NodeHighlighted):
        current_path: Path = event.node.data.path
        if current_path.is_dir():
            input: Input = self.query_one("Input")
            input.value = str(current_path)

    @on(Button.Pressed, "#single-choice-ok")
    def on_ok(self, event: Button.Pressed) -> None:
        """
        Return the user's choice back to the calling application and dismiss the dialog
        """
        input: Input = self.query_one("Input")
        self.dismiss(Path(input.value))


class ConfigFolder(ModalScreen[Path | None]):
    """Save to configuration."""

    DEFAULT_CSS = """
    ConfigFolder {
        align: center top;        
    }
    .dir_list {
        align: center top;
        width: 80;  # Width of the modal
        height: 20; # Height of the modal
        border: blue;
    }
    """

    def compose(self) -> ComposeResult:
        yield ConfigDir("~/", classes="dir_list")

    async def _on_key(self, event: events.Key) -> None:
        if event.name == "escape":
            self.dismiss(None)
        return super()._on_key(event)

    @on(DirectoryTree.DirectorySelected)
    def fd_selected(self, event: DirectoryTree.DirectorySelected):
        if not event.path.is_file():
            self.dismiss(event.path)
