import datetime
import time

from .site import Site


class Setting:
    def set(self, site: Site):
        pass


class ClickFieldSetting(Setting):
    def __init__(self, field: str):
        self._field = field

    def set(self, site: Site):
        site.click_field(self._field)


class WaitSetting(Setting):
    def __init__(self, duration: datetime.timedelta):
        self._duration = duration

    def set(self, site: Site):
        time.sleep(self._duration.total_seconds())


class ComboBoxSetting(Setting):
    def __init__(self, *, field_name=None, field_id=None, value=None):
        if field_id and field_name:
            raise ValueError(f"Both field_name ({field_name}) and field_id ({field_id}) cannot be specified")
        if not field_id and not field_name:
            raise ValueError("One of field_id or field_name must be specified")
        self._field_name = field_name
        self._field_id = field_id
        self._value = value

    def set(self, site: Site):
        if self._field_id:
            site.set_combo_box_value_by_id(self._field_id, self._value)
        if self._field_name:
            site.set_combo_box_value_by_name(self._field_name, self._value)


class DateSetting(Setting):
    def __init__(self, field: str, value: datetime.date, format: str = "%Y-%m-%d"):
        self._field = field
        self._value = value
        self._format = format

    def set(self, site: Site):
        site.set_value(self._field, self._value.strftime(self._format))


class TimeSetting(Setting):
    def __init__(self, field: str, value: datetime.datetime):
        self._field = field
        self._value = value

    def set(self, site: Site):
        site.set_value(self._field, self._value.strftime("%H:%M"))


class SubmissionSetting(Setting):
    def set(self, site: Site):
        site.submit()


class Setter:
    def __init__(self, site: Site):
        self._site = site

    @property
    def site(self):
        return self._site

    def set(self, path: str, *settings: Setting):
        self._site.go_to(path)
        time.sleep(2)
        for setting in settings:
            setting.set(self._site)
