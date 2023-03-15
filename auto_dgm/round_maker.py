import datetime
import time

from .site import Site


class RoundMaker:
    def __init__(self, site: Site, parent_id: int):
        self._site = site
        self._parent_id = parent_id

    def add_base_info_and_submit(self, date, title, comment):
        """ Fill in base info and create a new round.
        :return: New id of the created round
        """
        self._site.set_value("i01", date.strftime("%Y-%m-%d"))
        self._site.set_value("i02", date.strftime("%H:%M"))
        self._site.set_value("i03", title)
        self._site.set_value("i04", comment)
        self._site.set_combo_box_value_by_name("copy_players_from", "")
        time.sleep(1)
        self._site.submit()
        time.sleep(1)
        parameters = self._site.get_url_parameters()
        if 'message_ok' not in parameters:
            raise ValueError(f"Round not created successfully: {[(key, value) for key, value in parameters.items() if key.startswith('message')]}")
        return parameters['ID'][0]

    def create_multi_round_event(self, parent_id, date: datetime.datetime, title: str, comment: str):
        create_multi_round_event_url = f"u=competition_add&competitiontype=&parentid={parent_id}&record_type=4"
        self._site.go_to(create_multi_round_event_url)
        return self.add_base_info_and_submit(date, title, comment)

    def create_round(self, parent_id, date: datetime.datetime, title: str, comment: str):
        create_round_url = f"u=competition_add&competitiontype=&parentid={parent_id}&record_type=1"
        self._site.go_to(create_round_url)
        return self.add_base_info_and_submit(date, title, comment)
