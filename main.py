import datetime
import getpass
import os
import time
import typing

import dotenv
import selenium.webdriver.chrome.service
import yaml
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

import auto_dgm as ad

dotenv.load_dotenv()


def parse_timestamp(timestamp: str):
    return datetime.datetime.strptime(timestamp, "%H:%M")


def parse_timedelta(timestamp: str):
    time = parse_timestamp(timestamp)
    return datetime.timedelta(hours=time.hour, minutes=time.minute)


def get_start_time(round) -> datetime.time:
    if 'start_time' in round:
        start_time = round['start_time']
    elif 'groups' in round and len(round['groups']) > 0:
        start_time = round['groups'][0]["first_time"]
    else:
        raise ValueError("Expected either start_time or non-empty groups in config")
    return parse_timestamp(start_time).time()


def login(site: ad.Site):
    site.go_to("u=login")

    username = os.getenv("DGM_USERNAME", None)
    if not username:
        username = input("Username: ")

    password = os.getenv("DGM_PASSWORD", None)
    if not password:
        password = getpass.getpass()

    field = site.get_field_by_id("i01")
    field.send_keys(username)
    field = site.get_field_by_id("i02")
    field.send_keys(password)
    site.submit()
    time.sleep(2)


def get_registration(round: typing.Dict, event_date: datetime.datetime) -> ad.Registration:
    """
    :param round: The round configuration, where the only overridable setting is the registration end time.
    :param event_date: The event date, used as default.
    :return: Return the registration based on the round configuration, if present. Default
    to the event date - 6 days at midnight for start and the event date 23:00 as end.
    """
    registration_start = event_date - datetime.timedelta(days=6)
    registration_end = event_date.replace(hour=23)

    if "registration" in round:
        # Todo: Add start time configuration?
        if "end_time" in round["registration"]:
            end_time = parse_timestamp(round["registration"]["end_time"])
            registration_end = registration_end.replace(hour=end_time.hour, minute=end_time.minute)

    return ad.Registration(registration_start, registration_end)


def main(config, first_date: datetime.datetime, week_idx: int, headless: bool = False):
    options = webdriver.ChromeOptions()
    options.headless = headless
    driver = webdriver.Chrome(service=selenium.webdriver.chrome.service.Service(ChromeDriverManager().install()),
                              options=options)
    site = ad.Site(driver, "https://discgolfmetrix.com/")
    parent_id = config["main_event_id"]

    login(site)

    creator = ad.RoundMaker(site, parent_id)
    setter = ad.Setter(site)

    date = first_date.replace(hour=0, minute=0, second=0) + datetime.timedelta(days=week_idx * 7)
    weekly_round_id = creator.create_multi_round_event(parent_id, date, config["title_template"].format(week_idx + 1), config["comment"])

    weekly_round_settings = ad.WeeklyRoundSettings(weekly_round_id, config["is_weeklies"])
    for setting in weekly_round_settings:
        setter.set(setting.path, *setting.settings)

    for round in config["rounds"]:
        start_time = get_start_time(round)
        timedelta = datetime.timedelta(hours=start_time.hour, minutes=start_time.minute)
        round_id = creator.create_round(weekly_round_id, date + timedelta, round['title'], round['comment'])

        group_configs = None
        if "groups" in round:
            group_configs = [
                ad.AutoFillGroupTimeConfig(parse_timestamp(group["first_time"]),
                                           parse_timestamp(group["last_time"]),
                                           parse_timedelta(group["interval"]))
                for group in round["groups"]
            ]

        max_players_in_group = round.get("max_players_in_group", None)

        registration = get_registration(round, date)

        settings = ad.RoundSettings(round_id, registration, group_configs, max_players_in_group)
        for setting in settings:
            setter.set(setting.path, *setting.settings)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="The configuration file")
    parser.add_argument("--start-date",
                        type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'),
                        help="The start date for the first week")
    parser.add_argument("--week", type=int, help="The week number for the event. The first week has value 1")
    parser.add_argument("--headless", action="store_true", help="Run the application without showing GUI")

    args = parser.parse_args()

    with open(args.config) as file:
        yaml_config = yaml.safe_load(file)

    if args.week < 1:
        raise ValueError(f"The first week is week 1: {args.week}")

    main(yaml_config, args.start_date, args.week - 1, args.headless)
