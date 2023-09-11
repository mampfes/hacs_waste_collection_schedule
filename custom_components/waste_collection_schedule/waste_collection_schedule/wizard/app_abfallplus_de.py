#!/usr/bin/env python3
import site
from pathlib import Path

package_dir = Path(__file__).resolve().parents[2]
site.addsitedir(str(package_dir))
import inquirer
from waste_collection_schedule.service.AppAbfallplusDe import (SUPPORTED_APPS,
                                                               AppAbfallplusDe)

YAML = """
waste_collection_schedule:
    sources:
    - name: app_abfallplus_de
      args:
        app_id: {app_id}
        city: {city}
        strasse: {strasse}
        hnr: {hnr}
"""

bundesland = None
landkreis = None
city = None
street = None
house_number = None

calls = []


def select_bundesland(app: AppAbfallplusDe):
    bundeslaender = app.get_bundeslaender()
    print(bundeslaender)
    questions = [
        inquirer.List(
            "bundesland",
            choices=[(s["name"], s["name"]) for s in bundeslaender],
            message="Select your Bundesland",
        )
    ]
    bundesland = inquirer.prompt(questions)["bundesland"]
    calls.append(f"select_bundesland({bundesland})")
    app.select_bundesland(bundesland)
    return bundesland


def select_landkreis(app: AppAbfallplusDe):
    calls.append(f"get_landkreise()")
    landkreise = app.get_landkreise()
    questions = [
        inquirer.List(
            "landkreis",
            choices=[(s["name"], s["name"]) for s in landkreise] + [("BACK", "BACK")],
            message="Select your Landkreis",
        )
    ]
    landkreis = inquirer.prompt(questions)["landkreis"]
    if landkreis == "BACK":
        app.clear(0)
        select_bundesland(app)
        return select_landkreis(app)
    calls.append(f"select_landkreis({landkreis})")
    app.select_landkreis(landkreis)
    return landkreis


def select_city(app: AppAbfallplusDe, bund_select: bool):
    print("select_city")
    calls.append(f"get_kommunen()")

    cities = app.get_kommunen()
    print("cities:", cities)
    print("city_debug:", app.debug(), calls)

    questions = [
        inquirer.List(
            "city",
            choices=[(s["name"], s["name"]) for s in cities]
            + ([("BACK", "BACK")] if bund_select else []),
            message="Select your Kommune",
        )
    ]
    city = inquirer.prompt(questions)["city"]
    if city == "BACK":
        app.clear(1)
        select_landkreis(app)
        return select_city(app, bund_select)

    calls.append(f"select_kommune({city})")

    app.select_kommune(city)
    print("selected city:", city)
    return city


def select_street(app: AppAbfallplusDe, bund_select: bool):
    print("street_debug:", app.debug(), calls)

    street = None
    street_search = ""
    while street is None:
        questions = [
            inquirer.Text(
                "street_search",
                message="Search your street you will be given some options to choose from",
                default=street_search,
            )
        ]
        streets = app.get_streets(inquirer.prompt(questions)["street_search"])
        questions = [
            inquirer.List(
                "street",
                choices=[(s["name"], s["name"]) for s in streets] + [("BACK", "BACK")],
                message="Select your Street",
            )
        ]
        street = inquirer.prompt(questions)["street"]
        if street == "BACK":
            street = None

    if street == "BACK":
        app.clear(2)
        select_city(app, bund_select)
        return select_street(app, bund_select)
    calls.append(f"select_street({street})")

    app.select_street(street)
    return street


def select_house_number(app: AppAbfallplusDe, bund_select: bool):
    house_numbers = app.get_hnrs()
    questions = [
        inquirer.List(
            "house_number",
            choices=[(s["name"], s["name"]) for s in house_numbers]
            + [("BACK", "BACK")],
            message="Select your House Number",
        )
    ]
    house_number = inquirer.prompt(questions)["house_number"]
    if house_number == "BACK":
        app.clear(3)
        select_street(app, bund_select)
        return select_house_number(app, bund_select)
    app.select_hnr(house_number)
    return house_number


def main():
    questions = [
        inquirer.List(
            "app-id",
            choices=[(s, s) for s in SUPPORTED_APPS],
            message="Select your App",
        )
    ]
    app_id = inquirer.prompt(questions)["app-id"]

    app = AppAbfallplusDe(app_id, "", "", "")
    app.init_connection()
    calls.append(f"init_connection()")

    calls.append(f"get_kommunen()")
    cities = app.get_kommunen()
    bund_select = cities == []
    print("cities:", cities, bund_select)

    bundesland = landkreis = None
    if bund_select:
        bundesland = select_bundesland(app)
        landkreis = select_landkreis(app)
        # cities = app.get_kommunen()

    city = select_city(app, bund_select)
    street = select_street(app, bund_select)
    house_number = select_house_number(app, bund_select)

    yaml = YAML.format(
        app_id=app_id,
        city=city,
        strasse=street,
        hnr=house_number,
    )
    if bundesland:
        yaml += "        bundesland=bundesland,\n"
    if landkreis:
        yaml += "        landkreis=landkreis,\n"

    print(yaml)


if __name__ == "__main__":
    # app = AppAbfallplusDe("de.albagroup.app", "Braunschweig", "Hauptstraße", "7A")
    # print("START:", app.debug(), calls)
    # app.init_connection()
    # print("INIT:", app.debug(), calls)
    # print(app.get_kommunen())
    # print("got cities:", app.debug(), calls)
    # print(app.select_kommune("Braunschweig"))
    # print("selected:", app.debug(), calls)

    # print(app.get_streets())
    # print("got streets:", app.debug(), calls)

    # app = AppAbfallplusDe("de.albagroup.app", "Braunschweig", "", "")
    # app.init_connection()
    # print(app.init_connection())
    # print(app.get_kommunen() )
    # print(app.select_kommune("Braunschweig") )
    # print(app.get_streets())

    main()
