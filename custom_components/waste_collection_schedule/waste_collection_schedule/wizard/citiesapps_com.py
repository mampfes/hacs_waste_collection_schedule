#!/usr/bin/env python3
import site
from pathlib import Path

import inquirer

package_dir = Path(__file__).resolve().parents[2]
site.addsitedir(str(package_dir))

import waste_collection_schedule.service.CitiesAppsCom as CitiesAppsCom  # noqa: E402

app = CitiesAppsCom.CitiesApps()


def ask_city():
    cities = app.get_cities()
    cities.sort(key=lambda d: d["name"])

    questions = [
        inquirer.List(
            "city",
            choices=[(c["name"], c["_id"]) for c in cities],
            message="Select a city",
        )
    ]
    city_id = inquirer.prompt(questions)["city"]
    city = [c["name"] for c in cities if c["_id"] == city_id][0]

    return [city_id, city]


def ask_calendar(city_id, allow_search=True):
    calendars = app.get_garbage_calendars(city_id)
    if len(calendars) == 1:
        print("# Only one calendar found, using that one")
        cal = calendars[0]["name"]
    else:
        choices = [c["name"] for c in calendars]
        choices.sort()
        if allow_search:
            choices = ["Search By Street", *choices]
        questions = [
            inquirer.List(
                "cal",
                choices=choices,
                message="Select a calendar",
                default="Search By Street",
            )
        ]
        cal = inquirer.prompt(questions)["cal"]
    return cal


def ask_by_street(city_id):
    streets = app.get_streets(city_id)
    if not streets["streets"]:
        print("City does not support searching by street")
        return ask_calendar(city_id, allow_search=False)

    streetlist = streets["streets"]

    streetlist.sort(key=lambda d: d["full_names"])
    calendars = {
        s_cal["garbage_areaid"]: s_cal["name"] for s_cal in streets["calendars"]
    }
    choices = [
        (" ".join(c["full_names"]), calendars[c["areaids"][0]]) for c in streetlist
    ]
    questions = [inquirer.List("cal", choices=choices, message="Select a street")]
    return inquirer.prompt(questions)["cal"]


def main():
    city_id, city = ask_city()
    cal = ask_calendar(city_id)

    if cal == "Search By Street":
        cal = ask_by_street(city_id)

    print(
        f"""waste_collection_schedule:
    sources:
    - name: citiesapps_com
      args:
        city: {city}
        calendar: {cal}"""
    )


if __name__ == "__main__":
    main()
