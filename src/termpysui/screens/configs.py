#    Copyright Frank V. Castellucci
#    SPDX-License-Identifier: Apache-2.0

# -*- coding: utf-8 -*-

"""Configuration screen for App."""

from functools import partial
from pathlib import Path
from rich.text import Text
from textual import work
from textual.app import ComposeResult
from textual.coordinate import Coordinate
from textual.containers import Vertical, Container, Grid
from textual import on
from textual.reactive import reactive
from textual.screen import Screen
import textual.validation as validator
from textual.widgets import (
    DataTable,
    Footer,
    Header,
    Button,
)

from textual.widgets.data_table import RowKey

from ..modals.single_choice import SingleChoiceDialog
from ..modals.configfm import ConfigPicker, ConfigSaver
from ..modals.pyconfig_add import (
    AddGroup,
    AddIdentity,
    AddProfile,
    NewGroup,
    NewIdentity,
    NewProfile,
)
from ..widgets.editable_table import EditableDataTable, CellConfig
from pysui import PysuiConfiguration
from pysui.sui.sui_pgql.config.confgroup import ProfileGroup, Profile, ProfileAlias


class ConfigRow(Container):
    """Base configuration container class."""

    _CONFIG_ROWS: list["ConfigRow"] = []
    configuration: reactive[PysuiConfiguration | None] = reactive(
        None, always_update=True
    )
    configuration_group: reactive[ProfileGroup | None] = reactive(
        None, always_update=True
    )

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
            row.query_one("Button").disabled = False
            row.configuration = pysuicfg

    @classmethod
    def config_group_change(cls, pgroup: ProfileGroup) -> None:
        """Dispatch a change in the active group."""
        for row in cls._CONFIG_ROWS:
            row.configuration_group = pgroup

    def _switch_active(self, cell: EditableDataTable.CellValueChange) -> Coordinate:
        """Change the active row."""
        new_active_coord: Coordinate = None
        # The current was 'Active', find an alternative or ignore if solo
        if cell.old_value == "Yes":
            new_active_coord = cell.table.switch_active(
                (1, "Yes"), (1, "No"), set_focus=True
            )
        elif cell.new_value == "Yes":
            # Update existing Yes to No and set current to Yes
            name = str(cell.table.get_cell_at(cell.coordinates.left()))
            new_active_coord = cell.table.switch_active(
                (1, "Yes"), (0, name), set_focus=True
            )
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
        yield Button(
            "Add", variant="primary", compact=True, id="add_group", disabled=True
        )
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
        new_group: NewGroup = await self.app.push_screen_wait(AddGroup())
        if (
            new_group is not None
            and new_group.name not in self.configuration.group_names()
        ):
            table: EditableDataTable = self.query_one("#config_group")
            prf_grp = ProfileGroup(new_group.name, "", "", [], [], [], [])
            self.configuration.model.add_group(
                group=prf_grp, make_active=new_group.active
            )
            number = table.row_count + 1
            label = Text(str(number), style="#B0FC38 italic")
            table.add_row(
                *[Text(new_group.name), Text("No")],
                label=label,
            )
            if new_group.active:
                self.configuration.model.group_active = new_group.name
                table.switch_active((1, "Yes"), (0, new_group.name), set_focus=True)
            self.configuration.save()
            self.config_group_change(self.configuration.active_group)

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
                gname = str(cell.table.get_cell_at(new_coord))
                self.configuration.model.group_active = gname
                group = self.configuration.model.get_group(group_name=gname)
            self.configuration.save()
            self.config_group_change(group)

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
        yield Button(
            "Add", variant="primary", compact=True, id="add_profile", disabled=True
        )
        yield EditableDataTable(self._CP_EDITS, id="config_profile")

    @on(Button.Pressed, "#add_profile")
    async def on_add_profile(self, event: Button.Pressed) -> None:
        """
        Return the user's choice back to the calling application and dismiss the dialog
        """
        self.add_profile()

    @work()
    async def add_profile(self):
        new_profile: NewProfile = await self.app.push_screen_wait(AddProfile())
        if (
            new_profile is not None
            and new_profile.name not in self.configuration_group.profile_names
        ):
            table: EditableDataTable = self.query_one("#config_profile")
            prf = Profile(new_profile.name, new_profile.url)
            self.configuration_group.add_profile(
                new_prf=prf, make_active=new_profile.active
            )
            number = table.row_count + 1
            label = Text(str(number), style="#B0FC38 italic")
            table.add_row(
                *[Text(new_profile.name), Text("No"), Text(new_profile.url)],
                label=label,
            )
            if new_profile.active:
                table.switch_active((1, "Yes"), (0, new_profile.name), set_focus=True)
            self.configuration.save()
            # self.config_group_change(self.configuration.active_group)

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
                    cell.table.get_cell_at(active_coord)
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
        self.border_title = self.name
        if cfg:
            # Label it
            self.border_title = self.name + f" in {cfg.group_name}"
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
        yield Button(
            "Add", variant="primary", compact=True, disabled=True, id="add_identity"
        )
        yield EditableDataTable(self._CI_EDITS, id="config_identities")

    @on(Button.Pressed, "#add_identity")
    async def on_add_profile(self, event: Button.Pressed) -> None:
        """
        Return the user's choice back to the calling application and dismiss the dialog
        """
        self.add_identity()

    @work()
    async def add_identity(self):
        new_ident: NewIdentity = await self.app.push_screen_wait(AddIdentity())
        alias_list = [x.alias for x in self.configuration_group.alias_list]
        if new_ident is not None and new_ident.alias not in alias_list:
            table: EditableDataTable = self.query_one("#config_identities")
            mnem, addy, prfkey, prfalias = self.configuration_group.new_keypair_parts(
                of_keytype=new_ident.key_scheme,
                word_counts=new_ident.word_count,
                derivation_path=new_ident.derivation_path,
                alias=new_ident.alias,
                alias_list=alias_list,
            )
            print()
            # prf = Profile(new_profile.name, new_profile.url)
            # self.configuration_group.add_profile(
            #     new_prf=prf, make_active=new_profile.active
            # )
            # number = table.row_count + 1
            # label = Text(str(number), style="#B0FC38 italic")
            # table.add_row(
            #     *[Text(new_profile.name), Text("No"), Text(new_profile.url)],
            #     label=label,
            # )
            # if new_profile.active:
            #     table.switch_active((1, "Yes"), (0, new_profile.name), set_focus=True)
            # self.configuration.save()

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
                new_coord = self._switch_active(cell).right().right().right()
                addy = str(cell.table.get_cell_at(new_coord))
                self.configuration_group.using_address = addy
            self.configuration.save()

    def watch_configuration_group(self, cfg: ProfileGroup):
        table: EditableDataTable = self.query_one("#config_identities")
        # Empty table
        table.clear()
        self.border_title = self.name
        if cfg:
            self.border_title = self.name + f" in {cfg.group_name}"
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
