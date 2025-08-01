#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""New PysuiConfiguration Modal."""

import dataclasses
from pathlib import Path
from pathvalidate import ValidationError, validate_filepath

from textual import events, work
from textual.app import ComposeResult
from textual.containers import (
    Horizontal,
    HorizontalGroup,
    Vertical,
)
from textual.screen import ModalScreen
import textual.validation as validator
from textual.widgets import Input, Button, Header, SelectionList, Label
from .configfm import ConfigFolder


@dataclasses.dataclass
class NewConfig:
    config_path: Path
    setup_graphql: bool
    setup_grpc: bool


class NewConfiguration(ModalScreen[NewConfig | None]):
    """New Configuration Modal Screen."""

    DEFAULT_CSS = """
        NewConfiguration {
            
            align: center middle;

            & Vertical {
                width: 50%;
                height: 50%;
                background: $panel;
                border: $secondary round;       
                margin:1; 

                & Label {
                    align: center middle;
                    margin: 1;
                }

                & .group_gen {
                    margin: 1;
                    border: white;
                    width: 70%;
                    height: auto;
                }                    

                & .folder_set {
                    width: 80;  
                    height: auto;
                    align: left top;
                    margin: 1;
                    & Input {
                        width:70%;
                    }
                    & Button {
                        width: 20%;
                    }
                }

                & Horizontal {
                    align: center middle;
                    margin: 1 2;
                    & Button {
                        margin: 0 2;
                    }
                }
            }
        }    
    """
    TITLE = "Create a mew PysuiConfiguration"

    def _validate_dir(self, in_value: str) -> bool:
        """Ensure it is a valid directory structure."""
        if in_value and in_value[0] != "/":
            return False
        try:
            validate_filepath(in_value, platform="auto")
            return True
        except ValidationError as ve:
            return False

    def compose(self) -> ComposeResult:
        """
        Create the widgets for the new configation user interface
        """
        yield Vertical(
            Header(),
            Label(""),
            HorizontalGroup(
                Input(
                    placeholder="PysuiConfiguation Path",
                    validators=[
                        validator.Function(
                            self._validate_dir, "Invalid folder specification."
                        )
                    ],
                ),
                Button("select", variant="primary", id="dirlist"),
                classes="folder_set",
            ),
            SelectionList[int](
                ("GraphQL", "gql", True), ("gRPC", "grpc"), classes="group_gen"
            ),
            Horizontal(
                Button("OK", variant="primary", id="single-choice-ok"),
                Button("Cancel", variant="error", id="single-choice-cancel"),
            ),
            id="single-choice-dlg",
        )

    def on_mount(self, *widgets, before=None, after=None):
        self.query_one(".group_gen").border_title = "Generate groups for"

    # @on(Input.Changed, "#add_name")
    def on_input_changed(self, event: Input.Changed) -> None:
        """Check if validation error on name."""
        ilab = self.query_one(Label)
        if event.validation_result and not event.validation_result.is_valid:
            edesc = event.validation_result.failure_descriptions[0]
            ilab.update(f"[red]{edesc}")
        else:
            ilab.update("")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "single-choice-ok":
            gens = self.query_one(SelectionList).selected
            self.dismiss(
                NewConfig(
                    Path(self.query_one(Input).value), "gql" in gens, "grpc" in gens
                )
            )
        elif event.button.id == "single-choice-cancel":
            self.dismiss(None)
        elif event.button.id == "dirlist":
            self.new_conf_folder()

    @work()
    async def new_conf_folder(self) -> None:
        """Do the work for creatinig new configuration."""
        selected = await self.app.push_screen_wait(
            ConfigFolder(),
        )
        if selected:
            self.query_one(Input).value = str(selected)

    async def _on_key(self, event: events.Key) -> None:
        if event.name == "escape":
            self.dismiss(None)
