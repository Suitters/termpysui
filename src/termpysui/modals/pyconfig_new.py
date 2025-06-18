#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""New PysuiConfiguration Modal."""

from pathlib import Path
from textual import on, events
from textual.app import ComposeResult
from textual.containers import (
    Horizontal,
    VerticalGroup,
    HorizontalGroup,
    Center,
    Vertical,
)
from textual.screen import ModalScreen
from textual.widgets import Input, Button, Tree, Header, OptionList, Label


class NewConfiguration(ModalScreen[Path | None]):
    """New Configuration Modal Screen."""

    def compose(self) -> ComposeResult:
        """
        Create the widgets for the SingleChoiceDialog's user interface
        """
        yield Vertical(
            Header(),
            Center(Label("Setup for GraphQL", id="single-choice-label")),
            Center(Label("Setup for gRPC", id="single-choice-label")),
            Center(
                Horizontal(
                    Button("OK", variant="primary", id="single-choice-ok"),
                    Button("Cancel", variant="error", id="single-choice-cancel"),
                )
            ),
            id="single-choice-dlg",
        )

    def mount(self, *widgets, before=None, after=None):
        return super().mount(*widgets, before=before, after=after)

    async def _on_key(self, event: events.Key) -> None:
        if event.name == "escape":
            self.dismiss(None)
