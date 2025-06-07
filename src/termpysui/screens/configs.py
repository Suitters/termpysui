#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Configuration screen for App."""

import dataclasses
from functools import partial
from typing import Any, Callable, Iterable, Optional
from pathlib import Path
from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.coordinate import Coordinate
from textual.geometry import Offset, Region
from textual.containers import Vertical, Container, Grid
from textual import events, on
from textual.message import Message
from textual.reactive import reactive
from textual.screen import Screen, ModalScreen
import textual.validation as validator
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Button,
    Input,
    Pretty,
)

from ..modals.single_choice import SingleChoiceDialog
from ..modals.configfm import ConfigPicker, ConfigSaver
from ..modals.pyconfig_add import AddGroup, AddProfile
from pysui import PysuiConfiguration
from pysui.sui.sui_pgql.config.confgroup import ProfileGroup


class EditWidgetScreen(ModalScreen):
    """A modal screen with a single input widget."""

    CSS = """
        Input.-valid {
            border: tall $success 60%;
        }
        Input.-valid:focus {
            border: tall $success;
        }    
        Pretty {
            margin: 1 2;
        }        
        Input {
            border: solid $secondary-darken-3;
            padding: 0;

            &:focus {
                border: round $secondary;
            }
        }
    """

    def __init__(
        self,
        value: Any,
        region: Region,
        validators: validator.Validator | Iterable[validator.Validator] | None = None,
        *args,
        **kwargs,
    ) -> None:
        """Initialization.

        Args:
            value (Any): the original value.
            region (Region): the region available for the input widget contents.
        """
        super().__init__(*args, **kwargs)
        self.validators = validators if validators else []
        self.value = value
        # store type to later cast the new value to the old type
        self.value_type = type(value)
        self.widget_region = region

    def compose(self) -> ComposeResult:
        yield Input(
            value=str(self.value), validators=self.validators, validate_on=["submitted"]
        )
        yield Pretty([])

    def on_mount(self) -> None:
        """Calculate and set the input widget's position and size.

        This takes into account any padding you might have set on the input
        widget, although the default padding is 0.
        """
        input = self.query_one(Input)
        input.offset = Offset(
            self.widget_region.offset.x - input.styles.padding.left - 1,
            self.widget_region.offset.y - input.styles.padding.top - 1,
        )
        input.styles.width = (
            self.widget_region.width
            + input.styles.padding.left
            + input.styles.padding.right
            # include the borders _and_ the cursor at the end of the line
            + 3
        )
        input.styles.height = (
            self.widget_region.height
            + input.styles.padding.top
            + input.styles.padding.bottom
            # include the borders
            + 2
        )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Return the new value.

        The new value is cast to the original type. If that is not possible
        (e.g. you try to replace a number with a string), returns None to
        indicate that the cell should _not_ be updated.
        """
        try:
            if not event.validation_result.is_valid:
                self.query_one(Pretty).update(
                    event.validation_result.failure_descriptions
                )
            else:
                self.dismiss(self.value_type(event.value))
        except ValueError:
            self.dismiss(None)

    def _on_key(self, event: events.Key) -> None:
        """Allow escape for cancelling."""
        if event.name == "escape":
            self.dismiss(None)

        return super()._on_key(event)


@dataclasses.dataclass
class CellConfig:
    field_name: str
    editable: Optional[bool] = True
    inline: Optional[bool] = False
    validators: validator.Validator | Iterable[validator.Validator] = None
    dialog: Optional[Callable] = False


class EditableDataTable(DataTable):
    """A datatable where you can edit cells."""

    BINDINGS = [("e", "edit", "Edit Cell")]

    class CellValueChange(Message):

        def __init__(
            self,
            table: "EditableDataTable",
            cell_config: CellConfig,
            coordinates: Coordinate,
            old_value: str,
            new_value: str,
        ):
            self.table = table
            self.cell_config: CellConfig = cell_config
            self.coordinates: Coordinate = coordinates
            self.old_value: str = old_value
            self.new_value: str = new_value
            super().__init__()

    def __init__(self, edit_config: list[CellConfig], **kwargs):
        super().__init__(**kwargs)
        self.edit_config = edit_config

    async def action_edit(self) -> None:
        coords = self.cursor_coordinate
        edit_cfg = self.edit_config[coords.column]
        if edit_cfg.editable:
            if edit_cfg.inline:
                self.edit_cell(coordinate=coords, cfg=edit_cfg)
            elif edit_cfg.dialog:
                self.edit_dialog(coordinate=coords, cfg=edit_cfg)

    @work()
    async def edit_dialog(self, coordinate: Coordinate, cfg: CellConfig) -> None:
        old_value = str(self.get_cell_at(coordinate))
        new_value = await self.app.push_screen_wait(cfg.dialog())
        if new_value is not None:
            self.post_message(
                self.CellValueChange(self, cfg, coordinate, old_value, new_value)
            )

    @work()
    async def edit_cell(self, coordinate: Coordinate, cfg: CellConfig) -> None:
        """Edit cell contents.

        Args:
            coordinate (Coordinate): the coordinate of the cell to update.
        """
        region = self._get_cell_region(coordinate)
        # the region containing the cell contents, without padding
        contents_region = Region(
            region.x + self.cell_padding,
            region.y,
            region.width - 2 * self.cell_padding,
            region.height,
        )
        absolute_offset = self.screen.get_offset(self)
        absolute_region = contents_region.translate(absolute_offset)
        old_value_cell = self.get_cell_at(coordinate)

        new_value = await self.app.push_screen_wait(
            EditWidgetScreen(
                value=old_value_cell,
                region=absolute_region,
                validators=cfg.validators,
            )
        )
        if new_value is not None:
            self.post_message(
                self.CellValueChange(
                    self, cfg, coordinate, str(old_value_cell), str(new_value)
                )
            )

    def row_with_value(self, row_cell: int, value: str) -> Any:
        """."""

        def has_value(in_rowc):
            """."""
            if str(self.get_row(in_rowc.key)[row_cell]) == value:
                return True
            else:
                return False

        return list(filter(has_value, self.ordered_rows))


class ConfigRow(Container):
    """Base configuration container class."""

    _CONFIG_ROWS: list["ConfigRow"] = []
    configuration: reactive[PysuiConfiguration | None] = reactive(None)
    configuration_group: reactive[ProfileGroup | None] = reactive(None)

    def __init__(
        self, *children, name=None, id=None, classes=None, disabled=False, markup=True
    ):
        ConfigRow._CONFIG_ROWS.append(self)
        super().__init__(
            *children,
            name=name,
            id=id,
            classes=classes,
            disabled=disabled,
            markup=markup,
        )

    @classmethod
    def has_config(cls) -> bool | PysuiConfiguration:
        """."""
        for row in cls._CONFIG_ROWS:
            if not row.configuration:
                return False
            else:
                return row.configuration
        return False

    @classmethod
    def config_change(cls, config_path: Path) -> None:
        """Dispatch configuration change."""
        cpath = config_path.parent
        pysuicfg = PysuiConfiguration(from_cfg_path=cpath)
        for row in cls._CONFIG_ROWS:
            row.configuration = pysuicfg

    @classmethod
    def config_group_change(cls, pgroup: ProfileGroup) -> None:
        """Dispatch a change in the active group."""
        for row in cls._CONFIG_ROWS:
            row.configuration_group = pgroup

    def _switch_active(self, cell: EditableDataTable.CellValueChange) -> Coordinate:
        """Change the active row."""
        prev_y_row = cell.table.row_with_value(1, "Yes")[0]
        curr_n_rows = cell.table.row_with_value(1, "No")
        new_active_coord: Coordinate = None
        # The current was 'Active', find an alternative or ignore if solo
        if cell.old_value == "Yes":
            if len(curr_n_rows) > 1:
                # Set the current to No
                cell.table.update_cell_at(
                    cell.coordinates, cell.new_value, update_width=True
                )
                # Set new to Yes
                n_row = int(str(curr_n_rows[0].label)) - 1
                coord = Coordinate(row=n_row, column=1)
                cell.table.update_cell_at(coord, cell.old_value, update_width=True)
                # Get associated group names
                new_active_coord = coord
                # new_y_name = str(cell.table.get_cell_at(coord.left()))
        elif cell.new_value == "Yes":
            # Update existing Yes to No
            coord = Coordinate(row=int(str(prev_y_row.label)) - 1, column=1)
            cell.table.update_cell_at(coord, cell.old_value, update_width=True)
            # Set new Yes
            cell.table.update_cell_at(
                cell.coordinates, cell.new_value, update_width=True
            )
            # Get and set active group
            new_active_coord = cell.coordinates
        cell.table.move_cursor(row=new_active_coord.row, column=0)
        return new_active_coord


class ConfigGroup(ConfigRow):

    _CG_HEADER: tuple[str, str] = ("Name", "Active")
    _CG_EDITS: list[CellConfig] = [
        CellConfig("Name", True, True),
        CellConfig(
            "Active",
            True,
            False,
            None,
            partial(
                SingleChoiceDialog, "Switch State", "Change Group Active", ["Yes", "No"]
            ),
        ),
    ]

    def compose(self):
        yield Button("Add", variant="primary", compact=True, id="add_group")
        yield EditableDataTable(self._CG_EDITS, id="config_group")

    def validate_group_name(self, table: EditableDataTable, in_value: str) -> bool:
        """Validate no rename collision."""
        coordinate = table.cursor_coordinate
        pre_value = str(table.get_cell_at(coordinate))
        if pre_value == in_value:
            pass
        elif in_value in self.configuration.group_names():
            return False
        return True

    def on_mount(self) -> None:
        self.border_title = self.name
        table: EditableDataTable = self.query_one("#config_group")
        table.add_columns(*self._CG_HEADER)
        self._CG_EDITS[0].validators = [
            validator.Length(minimum=3, maximum=32),
            validator.Function(
                partial(self.validate_group_name, table), "Group name not unique."
            ),
        ]
        table.focus()

    @on(Button.Pressed, "#add_group")
    async def on_add_group(self, event: Button.Pressed) -> None:
        """
        Return the user's choice back to the calling application and dismiss the dialog
        """
        self.add_group()

    @work()
    async def add_group(self):
        new_group = await self.app.push_screen_wait(AddGroup())
        if new_group is not None:
            pass

    @on(EditableDataTable.CellValueChange)
    def cell_change(self, cell: EditableDataTable.CellValueChange):
        """When a cell changes"""
        if cell.old_value != cell.new_value:
            # Group has been renamed
            if cell.cell_config.field_name == "Name":
                group = self.configuration.model.get_group(group_name=cell.old_value)
                group.group_name = cell.new_value
                if self.configuration.model.group_active == cell.old_value:
                    self.configuration.model.group_active = cell.new_value
                cell.table.update_cell_at(
                    cell.coordinates, cell.new_value, update_width=True
                )
            # Active status changed
            elif cell.cell_config.field_name == "Active":
                new_coord = self._switch_active(cell)
                self.configuration.model.group_active = str(
                    cell.table.get_cell_at(new_coord.left())
                )
                self.config_group_change(self.configuration.active_group)

            self.configuration.save()

    def watch_configuration(self, cfg: PysuiConfiguration):
        """Called when a new configuration is selected."""
        if cfg:
            table: EditableDataTable = self.query_one("#config_group")
            # Empty table
            table.clear()
            # Iterate group names and capture the active group
            active_row = 0
            for number, group in enumerate(cfg.group_names(), start=1):
                label = Text(str(number), style="#B0FC38 italic")
                if group == cfg.active_group_name:
                    active = "Yes"
                    active_row = number - 1
                else:
                    active = "No"
                table.add_row(*[Text(group), Text(active)], label=label)
            # Select the active row/column
            table.move_cursor(row=active_row, column=0, scroll=True)
            # Notify group listeners
            self.config_group_change(cfg.active_group)

    @on(DataTable.CellSelected)
    def group_cell_select(self, selected: DataTable.CellSelected):
        """Handle selection."""
        # A different group is selected.
        if selected.coordinate.column == 0 and selected.coordinate.row >= 0:
            gval = str(selected.value)
            self.config_group_change(
                self.configuration.model.get_group(group_name=gval)
            )


class ConfigProfile(ConfigRow):

    _CP_HEADER: tuple[str, str] = ("Name", "Active", "URL")
    _CP_EDITS: list[CellConfig] = [
        CellConfig("Name", True, True),
        CellConfig(
            "Active",
            True,
            False,
            None,
            partial(SingleChoiceDialog, "Switch State", "Change Active", ["Yes", "No"]),
        ),
        CellConfig("URL", True, True, [validator.URL()]),
    ]

    def compose(self):
        yield Button("Add", variant="primary", compact=True, id="add_profile")
        yield EditableDataTable(self._CP_EDITS, id="config_profile")

    @on(Button.Pressed, "#add_profile")
    async def on_add_profile(self, event: Button.Pressed) -> None:
        """
        Return the user's choice back to the calling application and dismiss the dialog
        """
        self.add_profile()

    @work()
    async def add_profile(self):
        new_group = await self.app.push_screen_wait(AddProfile())
        if new_group is not None:
            pass

    def validate_profile_name(self, table: EditableDataTable, in_value: str) -> bool:
        """Validate no rename collision."""
        coordinate = table.cursor_coordinate
        pre_value = str(table.get_cell_at(coordinate))
        if pre_value == in_value:
            pass
        elif in_value in self.configuration_group.profile_names:
            return False
        return True

    def on_mount(self) -> None:
        self.border_title = self.name
        table: EditableDataTable = self.query_one("#config_profile")
        table.add_columns(*self._CP_HEADER)
        self._CP_EDITS[0].validators = [
            validator.Length(minimum=3, maximum=32),
            validator.Function(
                partial(self.validate_profile_name, table), "Profile name not unique."
            ),
        ]

    @on(EditableDataTable.CellValueChange)
    def cell_change(self, cell: EditableDataTable.CellValueChange):
        """When a cell changes"""
        if cell.old_value != cell.new_value:
            if cell.cell_config.field_name == "Name":
                profile = self.configuration_group.get_profile(
                    profile_name=cell.old_value
                )
                profile.profile_name = cell.new_value
                if self.configuration_group.using_profile == cell.old_value:
                    self.configuration_group.using_profile = cell.new_value
                cell.table.update_cell_at(
                    cell.coordinates, cell.new_value, update_width=True
                )
            elif cell.cell_config.field_name == "Active":
                active_coord = self._switch_active(cell)
                self.configuration_group.using_profile = str(
                    cell.table.get_cell_at(active_coord.left())
                )
            elif cell.cell_config.field_name == "URL":
                profile_name = cell.table.get_cell_at(cell.coordinates.left().left())
                profile = self.configuration_group.get_profile(
                    profile_name=str(profile_name)
                )
                profile.url = cell.new_value
                cell.table.update_cell_at(
                    cell.coordinates, cell.new_value, update_width=True
                )
            self.configuration.save()

    def watch_configuration_group(self, cfg: ProfileGroup):
        table: EditableDataTable = self.query_one("#config_profile")
        # Empty table
        table.clear()
        if cfg:
            # Setup row label
            counter = 1
            # Build content
            active_row = 0
            for profile in cfg.profiles:
                label = Text(str(counter), style="#B0FC38 italic")
                if profile.profile_name == cfg.using_profile:
                    active = "Yes"
                    active_row = counter - 1
                else:
                    active = "No"
                table.add_row(
                    *[Text(profile.profile_name), Text(active), Text(profile.url)],
                    label=label,
                )
                counter += 1
            # Select the active row/column
            table.move_cursor(row=active_row, column=0, scroll=True)


class ConfigIdentities(ConfigRow):

    _CI_HEADER: tuple[str, str, str] = ("Alias", "Active", "Public Key", "Address")
    _CI_EDITS: list[CellConfig] = [
        CellConfig("Alias", True, True),
        CellConfig(
            "Active",
            True,
            False,
            None,
            partial(SingleChoiceDialog, "Switch State", "Change Active", ["Yes", "No"]),
        ),
        CellConfig("Public Key", False),
        CellConfig("Address", False),
    ]

    def compose(self):
        yield Button("Add", variant="primary", compact=True)
        yield EditableDataTable(self._CI_EDITS, id="config_identities")

    def validate_alias_name(self, table: EditableDataTable, in_value: str) -> bool:
        """Validate no rename collision."""
        coordinate = table.cursor_coordinate
        pre_value = str(table.get_cell_at(coordinate))
        if pre_value == in_value:
            pass
        elif in_value in [x.alias for x in self.configuration_group.alias_list]:
            return False
        return True

    def on_mount(self) -> None:
        self.border_title = self.name
        table: EditableDataTable = self.query_one("#config_identities")
        self._CI_EDITS[0].validators = [
            validator.Length(minimum=3, maximum=64),
            validator.Function(
                partial(self.validate_alias_name, table), "Alias name not unique."
            ),
        ]
        table.add_columns(*self._CI_HEADER)

    @on(EditableDataTable.CellValueChange)
    def cell_change(self, cell: EditableDataTable.CellValueChange):
        """When a cell edit occurs"""
        if cell.old_value != cell.new_value:
            if cell.cell_config.field_name == "Alias":
                for pfa in self.configuration_group.alias_list:
                    if pfa.alias == cell.old_value:
                        pfa.alias = cell.new_value
                cell.table.update_cell_at(
                    cell.coordinates, cell.new_value, update_width=True
                )
            elif cell.cell_config.field_name == "Active":
                new_coord = self._switch_active(cell)
                self.configuration_group.using_address = str(
                    cell.table.get_cell_at(new_coord.right().right())
                )
            self.configuration.save()

    def watch_configuration_group(self, cfg: ProfileGroup):
        table: EditableDataTable = self.query_one("#config_identities")
        # Empty table
        table.clear()
        if cfg:
            # Setup row label
            counter = 1
            # Build content
            active_row = 0
            indexer = len(cfg.address_list)
            for i in range(indexer):
                label = Text(str(i + 1), style="#B0FC38 italic")
                alias = cfg.alias_list[i]
                addy = cfg.address_list[i]
                if addy == cfg.using_address:
                    active = "Yes"
                    active_row = i
                else:
                    active = "No"
                table.add_row(
                    *[
                        Text(alias.alias),
                        Text(active),
                        Text(alias.public_key_base64),
                        Text(addy),
                    ],
                    label=label,
                )
            # Select the active row/column
            table.move_cursor(row=active_row, column=0, scroll=True)


class PyCfgScreen(Screen[None]):
    """."""

    DEFAULT_CSS = """
    $background: black;
    $surface: black;

    #config-header {
        background:green;
    }
    #app-grid {
        layout: grid;
        grid-size: 1;
        grid-columns: 1fr;
        grid-rows: 1fr;
    }    
    #top-right {
        height: 100%;
        background: $panel;
    }    
    ConfigRow {
        padding: 1 1;
        border-title-color: green;
        border-title-style: bold;        
        width: 100%;
        border: white;
        background: $background;
        height:2fr;
        margin-right: 1;
    }
    EditableDataTable {
        border: gray;
        background:$background;
    }
    #config-list {
        border:green;
        background:$background;
    }
    """

    BINDINGS = [
        ("ctrl+f", "select", "Select PysuiConfig"),
        ("ctrl+s", "savecfg", "Save to new location"),
    ]

    def __init__(self, name: str = None, id: str = None, classes: str = None):
        self.config_sections = [
            ("Groups", ConfigGroup),
            ("Profiles", ConfigProfile),
            ("Identities", ConfigIdentities),
        ]
        super().__init__(name, id, classes)

    def compose(self) -> ComposeResult:
        yield Header(id="config-header")
        self.title = "Pysui Configuration: (ctrl+f to select)"
        with Grid(id="app-grid"):
            # yield ConfigSelection(id="config-list")
            with Vertical(id="top-right"):
                for section_name, section_class in self.config_sections:
                    yield section_class(name=section_name)
        yield Footer()

    async def action_savecfg(self) -> None:
        """Save configuration to new location."""
        self.save_to()

    @work()
    async def save_to(self) -> None:
        """Run save to modal dialog."""

        def check_selection(selected: Path | None) -> None:
            """Called when ConfigSaver is dismissed."""
            if selected:
                new_fq_path = selected / "PysuiConfig.json"
                _has_config = ConfigRow.has_config()
                if not _has_config:
                    cfg = PysuiConfiguration.initialize_config(
                        in_folder=selected,
                        init_groups=[
                            {
                                "name": PysuiConfiguration.SUI_USER_GROUP,
                                "graphql_from_sui": False,
                                "make_active": True,
                            }
                        ],
                    )

                else:
                    _has_config.save_to(selected)
                # Notify change
                self.title = f"Pysui Configuration: {new_fq_path}"
                ConfigRow.config_change(new_fq_path)

        self.app.push_screen(ConfigSaver(), check_selection)

    async def action_select(self) -> None:
        self.select_configuration()

    @work()
    async def select_configuration(self) -> None:
        """Run selection modal dialog."""

        def check_selection(selected: Path | None) -> None:
            """Called when ConfigPicker is dismissed."""
            if selected:
                self.title = f"Pysui Configuration: {selected}"
                ConfigRow.config_change(selected)

        self.app.push_screen(ConfigPicker(), check_selection)
