import dataclasses
import datetime
import enum
import time
import typing

import selenium.webdriver.support.ui

from .settings import (
    SubmissionSetting,
    TimeSetting,
    DateSetting,
    ClickFieldSetting,
    Setting,
    Site,
    ComboBoxSetting
)


@dataclasses.dataclass
class BundledSetting:
    name: str
    sub_path: str
    id: str
    settings: typing.List[Setting]

    @property
    def path(self):
        return f"u={self.sub_path}&ID={self.id}"


@dataclasses.dataclass
class AutoFillGroupTimeConfig:
    first_time: datetime.datetime
    last_time: datetime.datetime
    interval: datetime.timedelta

    @property
    def number_of_groups(self) -> int:
        return (self.last_time - self.first_time) // self.interval + 1


class CustomAccordianSetting(ClickFieldSetting):
    def __init__(self, field: str):
        super().__init__(field)

    def set(self, site: Site):
        # Select the Player Registration Form accordian
        site.execute_script('document.getElementById("accordion").children[2].children[0].children[0].click()')
        time.sleep(1)
        super().set(site)
        # Select the Details accordian
        site.execute_script('document.getElementById("accordion").children[0].children[0].children[0].click()')
        time.sleep(1)


class AutoFillGroupTimesSetting(Setting):
    def __init__(self, *configs: AutoFillGroupTimeConfig):
        self._configs = configs

    def set(self, site: Site):
        count = 0
        for config in self._configs:
            time = config.first_time
            # Set a new offset every time we enter a new config
            offset = count
            for i in range(1, config.number_of_groups + 1):
                site.set_first_value_by_attribute_name_and_value("data-group-number", i + offset, time.strftime("%H:%M"))
                time += config.interval
                count += 1
        site.get_field_by_id("gm-save").click()


class CustomAccordianSetting2(Setting):
    def __init__(self, id):
        self.id = id

    def set(self, site: Site):
        field = site.get_field_by_id(self.id)
        site.execute_script("arguments[0].click()", field)


class GroupStart(enum.Enum):
    SHOTGUN = 0
    TEE = 1
    FLEX = 2


class SetNumberOfGroupsSetting(Setting):
    def __init__(self, field_id, value):
        self.field_id = field_id
        self.value = value

    def set(self, site: Site):
        field = site.get_field_by_id(self.field_id)
        select = selenium.webdriver.support.ui.Select(field)
        select.select_by_value(str(self.value))
        time.sleep(3)
        site.refresh()
        time.sleep(3)


@dataclasses.dataclass
class Registration:
    start: datetime.datetime
    end: datetime.datetime


class WeeklyRoundSettings:
    def __init__(self, round_id: str, is_weeklies: bool):
        self._basic_settings = self._create_basic_settings(round_id) if is_weeklies else None

    def __iter__(self):
        settings = [self._basic_settings] if self._basic_settings else []
        return iter(settings)

    @staticmethod
    def _create_basic_settings(round_id: str):
        settings = [
            ClickFieldSetting("id_weekly1"),
            SubmissionSetting(),
        ]
        return BundledSetting(
            "Basic",
            "competition_edit",
            round_id,
            settings,
        )


class RoundSettings:
    def __init__(self,
                 round_id,
                 registration: Registration,
                 configs: typing.Sequence[AutoFillGroupTimeConfig] = None,
                 max_players_in_group: int = None,
                 ):
        configs = configs or []
        has_group_settings = len(configs) > 0
        self.round_id = round_id
        self._group_settings = self._create_group_settings(configs, max_players_in_group) if has_group_settings else None
        self._registration_settings = self._create_registration_settings(registration, ask_for_group=has_group_settings)
        self._registration_results_settings = self._create_registration_results_settings()

    def __iter__(self) -> typing.Iterable[BundledSetting]:
        settings = [self.group_settings] if self.group_settings else []
        settings += [self.registration_settings, self.registration_results_settings]
        return iter(settings)

    @property
    def group_settings(self) -> typing.Union[BundledSetting, None]:
        return self._group_settings

    @property
    def registration_settings(self) -> BundledSetting:
        return self._registration_settings

    @property
    def registration_results_settings(self) -> BundledSetting:
        return self._registration_results_settings

    def _create_group_settings(self,
                               configs: typing.Sequence[AutoFillGroupTimeConfig],
                               max_players_in_group: int = None):
        number_of_groups = sum(config.number_of_groups for config in configs)
        settings = [
            SetNumberOfGroupsSetting(field_id='i01', value=number_of_groups),
            ComboBoxSetting(field_id='i02', value=GroupStart.FLEX.value),
        ]

        if max_players_in_group:
            settings += [ComboBoxSetting(field_id='i03', value=max_players_in_group)]

        settings += [AutoFillGroupTimesSetting(*configs)]

        return BundledSetting(
            "Groups",
            "competition_edit_groups",
            self.round_id,
            settings
        )

    def _create_registration_settings(self, registration: Registration, *, ask_for_group: bool):
        settings = [
            ClickFieldSetting('id_registration_yes1'),
            DateSetting('i01', registration.start),
            TimeSetting('i02', registration.start),
            DateSetting('i03', registration.end),
            TimeSetting('i04', registration.end),
        ]

        if ask_for_group:
            # Note: Groups have to be defined before we can ask for them
            settings.append(CustomAccordianSetting('id_ask_group'))

        settings.append(SubmissionSetting())

        return BundledSetting(
            "Registration",
            "competition_edit_registration",
            self.round_id,
            settings
        )

    def _create_registration_results_settings(self):
        settings = [
            CustomAccordianSetting2("id_show_groups")
        ]

        return BundledSetting(
            "Results",
            "competition_edit_result",
            self.round_id,
            settings,
        )
