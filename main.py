import datetime

import selenium.webdriver.chrome.service
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager

import auto_dgm as ad


def main():
    driver = webdriver.Chrome(service=selenium.webdriver.chrome.service.Service(ChromeDriverManager().install()))
    site = ad.Site(driver, "https://discgolfmetrix.com/")
    parent_id = 2455221  # Test
    week_idx = 8
    main_comment = "THIS IS MAIN COMMENT"
    flex_title = "Flex"
    flex_comment = "SOME FLEX COMMENT"
    joint_start_title = "Fellesstart"
    joint_start_comment = "SOME JOIN START COMMENT"
    site.go_to("u=login")
    input("Please login...")

    creator = ad.RoundMaker(site, parent_id)
    first_date = datetime.datetime(2023, 3, 7, 0, 0)

    flex_timedelta = datetime.timedelta(hours=6)
    joint_start_timedelta = datetime.timedelta(hours=17)
    date = first_date + datetime.timedelta(days=week_idx * 7)
    weekly_round_id = creator.create_multi_round_event(parent_id, date, f"Runde {week_idx + 1}", main_comment)
    flex_round_id = creator.create_round(weekly_round_id, date + flex_timedelta, flex_title, flex_comment)
    joint_start_round_id = creator.create_round(weekly_round_id, date + joint_start_timedelta, joint_start_title, joint_start_comment)

    setter = ad.Setter(site)

    configs = [
        ad.AutoFillGroupTimeConfig(datetime.datetime(1, 1, 1, 8), datetime.datetime(1, 1, 1, 16), datetime.timedelta(minutes=15)),
        ad.AutoFillGroupTimeConfig(datetime.datetime(1, 1, 1, 18, 45), datetime.datetime(1, 1, 1, 22), datetime.timedelta(minutes=15)),
    ]
    flex_settings = ad.RoundSettings(flex_round_id, date, 5, configs)
    joint_start_settings = ad.RoundSettings(joint_start_round_id, date, 5)

    for setting in (*flex_settings, *joint_start_settings):
        setter.set(setting.path, *setting.settings)
    # configure_flex(flex_round_id, date, setter)
    # configure_joint_start(joint_start_round_id, date, setter)


if __name__ == '__main__':
    main()
