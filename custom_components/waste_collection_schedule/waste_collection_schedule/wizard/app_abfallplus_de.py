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
        bundesland: {bundesland} 
        landkreis: {landkreis}
"""

bundesland = None
landkreis = None
city = None
street = None
house_number = None


def select_bundesland(app):
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
    app.select_bundesland(bundesland)
    return bundesland


def select_landkreis(app):
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
        select_bundesland(app)
        return select_landkreis(app)
    app.select_landkreis(landkreis)
    return landkreis


def select_city(app, bund_select):
    cities = app.get_kommunen()
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
        select_landkreis(app)
        return select_city(app, bund_select)

    app.select_kommune(city)
    return city


def select_street(app, bund_select):
    streets = app.get_streets()
    questions = [
        inquirer.List(
            "street",
            choices=[(s["name"], s["name"]) for s in streets] + [("BACK", "BACK")],
            message="Select your Street",
        )
    ]
    street = inquirer.prompt(questions)["street"]
    if street == "BACK":
        select_city(app, bund_select)
        return select_street(app, bund_select)
    app.select_street(street, bund_select)
    return street


def select_house_number(app, bund_select):
    house_numbers = app.get_house_numbers()
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
        select_street(app, bund_select)
        return select_house_number(app, bund_select)
    app.select_house_number(house_number)
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

    cities = app.get_kommunen()
    bund_select = cities == []
    print("cities:", cities, bund_select)

    if bund_select:
        bundesland = select_bundesland(app)
        landkreis = select_landkreis(app)
        cities = app.get_kommunen()

    city = select_city(app, bund_select)
    street = select_street(app, bund_select)
    house_number = select_house_number(app, bund_select)

    yaml = YAML.format(
        app_id=app_id,
        city=city,
        strasse=street,
        hnr=house_number,
        bundesland=bundesland,
        landkreis=landkreis,
    )
    print(yaml)


if __name__ == "__main__":
    main()
