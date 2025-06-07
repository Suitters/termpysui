#
"""Dashboard screen for App."""

from textual.app import App, ComposeResult
from textual.screen import Screen
from textual.widgets import Footer, Placeholder


class GraphQLScreen(Screen):
    """."""

    def compose(self) -> ComposeResult:
        yield Placeholder("GraphQL Screen")
        yield Footer()
