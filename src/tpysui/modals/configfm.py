#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Configuration file management modals."""

import dataclasses

from pathlib import Path
from typing import Iterable, Optional, cast
from textual import events, on
from textual.app import ComposeResult
from textual.containers import Horizontal, VerticalGroup, HorizontalGroup
from textual.screen import ModalScreen
from textual.widgets import DirectoryTree, Input, Button, Tree, RadioButton, Checkbox


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
        self,
        config_accept: str,
        name: Optional[str] = None,
        id: Optional[str] = None,
        classes: Optional[str] = None,
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

    async def _on_key(self, event: events.Key) -> None:
        if event.name == "escape":
            self.dismiss(None)

    @on(Tree.NodeHighlighted)
    def ft_selected(self, event: Tree.NodeHighlighted):
        current_path: Path = event.node.data.path  # type: ignore
        if current_path.is_dir():
            input: Input = cast(Input, self.query_one("Input"))
            input.value = str(current_path)

    @on(Button.Pressed, "#single-choice-ok")
    def on_ok(self, event: Button.Pressed) -> None:
        """
        Return the user's choice back to the calling application and dismiss the dialog
        """
        input: Input = cast(Input, self.query_one("Input"))
        self.dismiss(Path(input.value))


@dataclasses.dataclass
class GenSpec:
    fpath: Path
    client_type: str
    async_protocol: bool
    force: Optional[bool] = False


class ConfigGener(ModalScreen[GenSpec | None]):
    """Generate for python."""

    DEFAULT_CSS = """
    ConfigGener {
        align: center top;        
    }
    .gen_popup {
        border: blue 40%;
        align: center top;
        width: 80;  # Width of the modal
        height: 40; # Height of the modal
    }
    .easy_white {
        border: white 40%;
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

    def __init__(self, name=None, id=None, classes=None):
        super().__init__(name, id, classes)
        self._pressed_button: RadioButton | None = None

    def compose(self) -> ComposeResult:
        with VerticalGroup(classes="gen_popup"):
            with HorizontalGroup():
                yield Input(placeholder=str(Path.home()), classes="input")
                yield Button(
                    "Gen To",
                    variant="primary",
                    classes="button",
                    id="single-choice-ok",
                )
            yield Checkbox(
                "Force File Overwrite", value=False, id="force", classes="easy_white"
            )
            with HorizontalGroup(classes="easy_white"):
                yield RadioButton("GraphQL Sync", id="gql_sync", value=True)
                yield RadioButton("GraphQL Async", id="gql_async")
                yield RadioButton("gRPC Async", id="grpc_async")

            yield ConfigDir(str(Path.home()), classes="easy_white")

    def on_mount(self, event):
        self._pressed_button = cast(RadioButton, self.query_one("#gql_sync"))

    async def _on_key(self, event: events.Key) -> None:
        if event.name == "escape":
            self.dismiss(None)

    @on(RadioButton.Changed)
    def _handle_rb_change(self, event: RadioButton.Changed) -> None:
        """Respond to the value of a button in the set being changed.

        Args:
            event: The event.
        """
        event.stop()
        with self.prevent(RadioButton.Changed):
            # If the message pertains to a button being clicked to on...
            if event.radio_button.value:
                # If there's a button pressed right now and it's not really a
                # case of the user mashing on the same button...
                if (
                    self._pressed_button is not None
                    and self._pressed_button != event.radio_button
                ):
                    self._pressed_button.value = False
                # Make the pressed button this new button.
                self._pressed_button = event.radio_button
            else:
                # We're being clicked off, we don't want that.
                event.radio_button.value = True

    @on(Tree.NodeHighlighted)
    def ft_selected(self, event: Tree.NodeHighlighted):
        current_path: Path = event.node.data.path  # type: ignore
        input: Input = cast(Input, self.query_one("Input"))
        input.value = str(current_path)

    @on(Button.Pressed, "#single-choice-ok")
    def on_ok(self, event: Button.Pressed) -> None:
        """
        Return the user's choice back to the calling application and dismiss the dialog
        """
        input: Input = cast(Input, self.query_one("Input"))
        cb_force: Checkbox = cast(Checkbox, self.query_one("#force"))
        if not input.value or input.value.endswith(".py") is False:
            input.focus()
        else:
            client_type: str = ""
            if "gql" in self._pressed_button.id:  # type: ignore
                client_type = "GraphQL"
            else:
                client_type = "gRPC"
            self.dismiss(
                GenSpec(
                    Path(input.value).expanduser(),
                    client_type,
                    True if "async" in self._pressed_button.id else False,  # type: ignore
                    cb_force.value,
                )
            )


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

    @on(DirectoryTree.DirectorySelected)
    def fd_selected(self, event: DirectoryTree.DirectorySelected):
        if not event.path.is_file():
            self.dismiss(event.path)
