#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Termpysui TUI Application."""

from textual.app import App
from .screens import PyCfgScreen
from textual.binding import Binding


class TermPysuiApp(App):
    """A Textual app to manage configurations."""

    # BINDINGS = [
    #     Binding("c", "switch_mode('configs')", "Configs", show=False),
    # ]
    MODES = {
        "configs": lambda: PyCfgScreen(),
    }

    def on_mount(self) -> None:
        self.switch_mode("configs")


def main():
    app = TermPysuiApp()
    app.run()


if __name__ == "__main__":
    main()
