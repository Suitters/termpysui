#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Pysui Configuration Add Modals."""

import dataclasses

from textual import events, on
from textual.containers import (
    Horizontal,
    Vertical,
    Center,
)
from textual.screen import ModalScreen
import textual.validation as validator
from textual.widgets import Input, Button, Checkbox, Header, RadioSet

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


class AddGroup(ModalScreen[NewGroup | None]):
    """Add group dialog that accepts a name and active flag."""

    DEFAULT_CSS = """
    AddGroup {
        width: 50%;
        align: center top;    
        background: $primary 10%;   
        border: white; 
    }
    #add-group-dlg {
        width: 50%;
        height: 40%;
        border: white 80%;
        content-align: center top;
        margin: 1;
    }
    .center {
        content-align: center top;
    }
    .group_input {
        margin:1;
    }
    Button {
        width: 20%;
        margin: 1;
    }
    """

    TITLE = "Add a new Group"

    def compose(self):
        yield Vertical(
            Header(id="add_group_header"),
            Input(
                placeholder="Enter group name (3-32 chars)",
                classes="group_input",
                validators=[validator.Regex("^[a-zA-Z_-]{3,32}$")],
                id="group_name",
            ),
            Checkbox("Make Active?"),
            Center(
                Horizontal(
                    Button("OK", variant="primary", id="choice-ok"),
                    Button("Cancel", variant="error", id="choice-cancel"),
                )
            ),
            id="add-group-dlg",
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
        iput = self.query_one("Input")
        if not iput.value:
            iput.focus()
        else:
            self.dismiss(NewGroup(iput.value, self.query_one("Checkbox").value))

    @on(Button.Pressed, "#choice-cancel")
    def on_cancel(self, event: Button.Pressed) -> None:
        """
        Returns None to the calling application and dismisses the dialog
        """
        self.dismiss(None)


class AddProfile(ModalScreen[NewProfile | None]):
    """Add profile dialog that accepts a name, url and active flag."""

    DEFAULT_CSS = """
    AddProfile {
        width: 50%;
        align: center top;    
        background: $primary 10%;   
        border: white; 
    }
    #add-profile-dlg {
        width: 50%;
        height: 50%;
        border: white 80%;
        content-align: center top;
        margin: 1;
    }
    .center {
        content-align: center top;
    }
    .profile_input {
        margin:1;
    }
    Button {
        width: 20%;
        margin: 1;
    }
    """

    TITLE = "Add a new Profile"

    def compose(self):
        yield Vertical(
            Header(id="add_profile_header"),
            Input(
                placeholder="Enter profile name (3-32 chars)",
                classes="profile_input",
                validators=[validator.Regex("^[a-zA-Z_-]{3,32}$")],
                id="profile_name",
            ),
            Input(
                placeholder="Enter profile URL",
                classes="profile_input",
                validators=[validator.URL()],
                id="profile_url",
            ),
            Checkbox("Make Active?"),
            Center(
                Horizontal(
                    Button("OK", variant="primary", id="choice-ok"),
                    Button("Cancel", variant="error", id="choice-cancel"),
                )
            ),
            id="add-profile-dlg",
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
        iput = self.query_one("#profile_name")
        if not iput.value:
            iput.focus()
        iurl = self.query_one("#profile_url")
        if not iurl.value:
            iurl.focus()
        else:
            self.dismiss(
                NewProfile(iput.value, iurl.value, self.query_one("Checkbox").value)
            )

    @on(Button.Pressed, "#choice-cancel")
    def on_cancel(self, event: Button.Pressed) -> None:
        """
        Returns None to the calling application and dismisses the dialog
        """
        self.dismiss(None)


# Alias name, key scheme type, word count and derivation path
class AddIdentity(ModalScreen[NewIdentity | None]):
    """Add identity dialog that key provisioning directives."""

    TITLE = "Add a new Identity"

    DEFAULT_CSS = """
    AddIdentity {
        width: 50%;
        align: center top;    
        background: $primary 10%;   
        border: white; 
    }
    #add-identity-dlg {
        width: 50%;
        height: 65%;
        border: white 80%;
        content-align: center top;
        # margin: 1;
    }
    RadioSet Checkbox {
        margin: 1;
    }
    .center {
        content-align: center top;
    }
    .id_input {
        margin:1;
    }
    Button {
        width: 20%;
        margin: 1;
    }
    """

    def compose(self):
        self.ktindex = -1
        yield Vertical(
            Header(id="add_identity_header"),
            Input(
                placeholder="Enter identity alias (3-32 chars)",
                classes="id_input",
                validators=[validator.Regex("^[a-zA-Z_-]{3,32}$")],
                id="id_alias",
            ),
            RadioSet("ED25519", "SECP256K1", "SECP256R1", id="id_keytype"),
            Input(
                placeholder="Enter word count (i.e. 12,15,18,21,24), defaults to 12",
                classes="id_input",
                type="integer",
                max_length=2,
                validators=[validator.Regex(r"^12$|^15$|^18$|^21$|^24$")],
                valid_empty=True,
                id="id_word_count",
            ),
            Input(
                placeholder="Optional derivation path",
                classes="id_input",
                # validators=[validator.URL()],
                id="id_derv",
            ),
            Checkbox("Make Active?"),
            Center(
                Horizontal(
                    Button("OK", variant="primary", id="choice-ok"),
                    Button("Cancel", variant="error", id="choice-cancel"),
                )
            ),
            id="add-identity-dlg",
        )

    def on_radio_set_changed(self, event: RadioSet.Changed) -> None:
        self.ktindex = event.radio_set.pressed_index

    def _on_key(self, event: events.Key) -> None:
        if event.name == "escape":
            self.dismiss(None)
        return super()._on_key(event)

    @on(Button.Pressed, "#choice-ok")
    def on_ok(self, event: Button.Pressed) -> None:
        """
        Return the user's choice back to the calling application and dismiss the dialog
        """
        ialias = self.query_one("#id_alias")
        if not ialias.value:
            ialias.focus()
            ialias = None

        if self.ktindex < 0:
            self.query_one("#id_keytype").focus()

        idwc = self.query_one("#id_word_count").value
        if not idwc:
            idwc = 12

        iderv = self.query_one("#id_derv").value
        if ialias:
            self.dismiss(
                NewIdentity(
                    ialias.value,
                    SignatureScheme(self.ktindex),
                    idwc,
                    iderv,
                    self.query_one("Checkbox").value,
                )
            )

    @on(Button.Pressed, "#choice-cancel")
    def on_cancel(self, event: Button.Pressed) -> None:
        """
        Returns None to the calling application and dismisses the dialog
        """
        self.dismiss(None)
