#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pysui Configuration Add Modals."""

import dataclasses
import re
from textual.app import ComposeResult
from textual import events, on
from textual.containers import (
    Horizontal,
    VerticalScroll,
    Center,
)
from textual.screen import ModalScreen, ScreenResultType
import textual.validation as validator
from textual.widget import Widget
from textual.widgets import (
    Input,
    Button,
    Checkbox,
    Header,
    Select,
    Label,
)

from pysui.abstracts.client_keypair import SignatureScheme


@dataclasses.dataclass
class NewGroup:
    name: str
    active: bool


@dataclasses.dataclass
class NewProfile:
    name: str
    url: str
    active: bool


# Alias name, key scheme type, word count and derivation path and active
@dataclasses.dataclass
class NewIdentity:
    alias: str
    key_scheme: SignatureScheme
    word_count: int
    derivation_path: str
    active: bool


class AddBase(ModalScreen[ScreenResultType]):

    DEFAULT_CSS = """
    AddBase {
        align: center middle;    
        background: $primary 10%;   
        margin: 1;
    }
    VerticalScroll {
        width: 50%;
        height: 70%;
        border: white 80%;
        content-align: center middle;
        margin: 1;
    }
    Label {
        margin: 1;
    }
    .center {
        content-align: center middle;
    }
    .input_field {
        margin:1;
    }
    .margin_one {
        margin:1;
    }
    Button {
        width: 20%;
        height: 20%;
        margin: 1;        
    }
    """

    def __init__(self, config_names: list[str], name=None, id=None, classes=None):
        super().__init__(name, id, classes)
        self.names = config_names or []
        self.is_name_valid = False

    def _validate_name(self, in_value: str) -> bool:
        """."""
        self.is_name_valid = True
        if in_value in self.names:
            self.is_name_valid = False
        return self.is_name_valid

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Header(),
            Center(Label("", classes="center")),
            Input(
                placeholder="Enter name (3-32 chars)",
                classes="input_field",
                max_length=32,
                validators=[
                    validator.Regex("^[a-zA-Z_-]{3,32}$"),
                    validator.Function(self._validate_name, "Name already exists."),
                ],
                id="add_name",
            ),
            Checkbox(
                "Make Active?", compact=True, button_first=False, classes="margin_one"
            ),
            Center(
                Horizontal(
                    Button("OK", variant="primary", id="choice-ok"),
                    Button("Cancel", variant="error", id="choice-cancel"),
                )
            ),
            id="add-dlg",
        )

    def post_mount(self, event: events.Mount, container: Widget) -> None:
        pass

    def _on_mount(self, event: events.Mount) -> None:
        container = self.query_one(VerticalScroll)
        self.post_mount(event, container)
        self.query_one("#add_name").focus()

    async def _on_key(self, event: events.Key) -> None:
        if event.name == "escape":
            self.dismiss(None)

    @on(Input.Changed, "#add_name")
    def on_input_changed(self, event: Input.Changed) -> None:
        """Check if validation error on name."""
        ilab = self.query_one(Label)
        if event.validation_result and not event.validation_result.is_valid:
            edesc = event.validation_result.failure_descriptions[0]
            ilab.update(f"[red]{edesc}")
        else:
            ilab.update("")

    @on(Button.Pressed, "#choice-cancel")
    def on_cancel(self, event: Button.Pressed) -> None:
        """
        Returns None to the calling application and dismisses the dialog
        """
        self.dismiss(None)


class AddGroup(AddBase[NewGroup | None]):
    """Add group dialog that accepts a name and active flag."""

    TITLE = "Add a new Group"

    def post_mount(self, event: events.Mount, container: Widget) -> None:
        """Called post mount for adding new widgets."""
        return

    @on(Button.Pressed, "#choice-ok")
    def on_ok(self, event: Button.Pressed) -> None:
        """
        Return the user's choice back to the calling application and dismiss the dialog
        """
        iput = self.query_one("#add_name", Input)
        if not iput.value or self.is_name_valid == False:
            iput.focus()
        else:
            self.dismiss(NewGroup(iput.value, self.query_one(Checkbox).value))


class AddProfile(AddBase[NewProfile | None]):
    """Add profile dialog that accepts a name, url and active flag."""

    TITLE = "Add a new Profile"
    REGGIE = re.compile(
        (
            "((http|https)://)(www.)?"
            + "[a-zA-Z0-9@:%._\\\\+~#?&amp;//=]"
            + "{2,256}\\\\.[a-z]"
            + "{2,6}\\\\b([-a-zA-Z0-9@:%"
            + "._\\\\+~#?&amp;//=]*)"
        )
    )

    def post_mount(self, event: events.Mount, container: Widget) -> None:
        """Called post mount for adding new widgets."""
        for idx, widg in enumerate(container.children):
            if isinstance(widg, Checkbox):
                container.mount(
                    Input(
                        placeholder="Enter profile URL",
                        classes="input_field",
                        validators=[validator.Regex(self.REGGIE)],
                        id="profile_url",
                    ),
                    before=idx,
                )
                break

    @on(Button.Pressed, "#choice-ok")
    def on_ok(self, event: Button.Pressed) -> None:
        """
        Return the user's choice back to the calling application and dismiss the dialog
        """
        iput = self.query_one("#add_name", Input)
        if not iput.value:
            iput.focus()
            return
        iurl = self.query_one("#profile_url", Input)
        if not iurl.value:
            iurl.focus()
            return
        is_active = self.query_one(Checkbox).value if self.names else True
        self.dismiss(NewProfile(iput.value, iurl.value, is_active))


# Alias name, key scheme type, word count and derivation path
class AddIdentity(AddBase[NewIdentity | None]):
    """Add identity dialog that key provisioning directives."""

    TITLE = "Add a new Identity"

    def __init__(self, config_names, name=None, id=None, classes=None):
        super().__init__(config_names, name, id, classes)
        self.ktindex = -1

    def post_mount(self, event: events.Mount, container: Widget) -> None:
        """Called post mount for adding new widgets."""
        key_types = (
            ["Ed25519", 0],
            ["Secp256k1", 1],
            ["Secp256r1", 2],
        )
        for idx, widg in enumerate(container.children):
            if isinstance(widg, Checkbox):
                container.mount(
                    Select(
                        key_types,
                        prompt="Select a Key type",
                        tooltip="The type used for generating a private key",
                        id="id_keytype",
                        classes="margin_one",
                    ),
                    Input(
                        placeholder="Enter word count (i.e. 12,15,18,21,24), defaults to 12",
                        classes="input_field",
                        type="integer",
                        max_length=2,
                        validators=[validator.Regex(r"^12$|^15$|^18$|^21$|^24$")],
                        valid_empty=True,
                        id="id_word_count",
                    ),
                    Input(
                        placeholder="Optional derivation path",
                        classes="input_field",
                        id="id_derv",
                    ),
                    before=idx,
                )
                break

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        self.ktindex = event.value

    @on(Button.Pressed, "#choice-ok")
    def on_ok(self, event: Button.Pressed) -> None:
        """
        Return the user's choice back to the calling application and dismiss the dialog
        """
        ialias: Input = self.query_one("#add_name", Input)
        if not ialias.value or self.is_name_valid == False:
            ialias.focus()
            return

        if 0 <= self.ktindex <= 2:
            self.query_one("#id_keytype").focus()

        idwc = self.query_one("#id_word_count", Input).value
        if not idwc:
            idwc = 12

        is_active = self.query_one(Checkbox).value if self.names else True

        iderv = self.query_one("#id_derv", Input).value
        if ialias:
            self.dismiss(
                NewIdentity(
                    ialias.value,
                    SignatureScheme(self.ktindex),
                    int(idwc),
                    iderv,
                    is_active,
                )
            )
