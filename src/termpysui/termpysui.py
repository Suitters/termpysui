#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Termpysui TUI Application."""

from textual.app import App
from .screens import PyCfgScreen, GraphQLScreen


class TermPysuiApp(App):
    """A Textual app to manage configurations."""

    BINDINGS = [
        ("c", "switch_mode('configs')", "Configs"),
        ("g", "switch_mode('graphql')", "GraphQL"),
    ]
    MODES = {
        "configs": PyCfgScreen,  # type: ignore
        "graphql": GraphQLScreen,
    }

    def on_mount(self) -> None:
        self.switch_mode("configs")


def main():
    app = TermPysuiApp()
    app.run()


if __name__ == "__main__":
    main()
