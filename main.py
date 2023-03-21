import datetime
import getpass
import os
import time

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


def main(config, first_date: datetime.datetime, week_idx: int):
    driver = webdriver.Chrome(service=selenium.webdriver.chrome.service.Service(ChromeDriverManager().install()))
    site = ad.Site(driver, "https://discgolfmetrix.com/")
    parent_id = config["main_event_id"]

    login(site)

    creator = ad.RoundMaker(site, parent_id)
    setter = ad.Setter(site)

    date = first_date.replace(hour=0, minute=0, second=0) + datetime.timedelta(days=week_idx * 7)
    weekly_round_id = creator.create_multi_round_event(parent_id, date, config["title_template"].format(week_idx + 1), config["comment"])

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

        settings = ad.RoundSettings(round_id, date, group_configs, max_players_in_group)
        for setting in settings:
            setter.set(setting.path, *setting.settings)


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("-c", "--config", help="The configuration file")
    parser.add_argument("--start-date",
                        type=lambda s: datetime.datetime.strptime(s, '%Y-%m-%d'),
                        help="The start date for the first week")
    parser.add_argument("--week", type=int, help="The 0-based index for the event")

    args = parser.parse_args()

    with open(args.config) as file:
        yaml_config = yaml.safe_load(file)

    main(yaml_config, args.start_date, args.week)
