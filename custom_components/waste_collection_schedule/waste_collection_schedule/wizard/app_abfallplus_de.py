#!/usr/bin/env python3
import site
from pathlib import Path
from typing import Tuple

import inquirer

package_dir = Path(__file__).resolve().parents[2]
site.addsitedir(str(package_dir))
import waste_collection_schedule.service.AppAbfallplusDe as AppAbfallplusDe  # noqa: E402

YAML = {
    "base": """
waste_collection_schedule:
    sources:
    - name: app_abfallplus_de
      args:
        app_id: {app_id}
        city: {city}""",
    "bezirk": """
        bezirk: {bezirk}""",
    "street": """
        strasse: {strasse}""",
    "hnr": """
        hnr: {hnr}""",
    "bundesland": """
        bundesland: {bundesland}""",
    "landkreis": """
        landkreis: {landkreis}""",
}


def select_bundesland(app: AppAbfallplusDe.AppAbfallplusDe):
    bundeslaender = app.get_bundeslaender()
    questions = [
        inquirer.List(
            "bundesland",
            choices=sorted([(s["name"], s["name"]) for s in bundeslaender]),
            message="Select your Bundesland",
        )
    ]
    bundesland = inquirer.prompt(questions)["bundesland"]
    app.select_bundesland(bundesland)
    return bundesland


def select_landkreis(app: AppAbfallplusDe.AppAbfallplusDe):
    landkreise = app.get_landkreise()
    questions = [
        inquirer.List(
            "landkreis",
            choices=sorted(
                [(s["name"], s["name"]) for s in landkreise] + [("BACK", "BACK")]
            ),
            message="Select your Landkreis",
        )
    ]
    landkreis = inquirer.prompt(questions)["landkreis"]
    if landkreis == "BACK":
        app.clear(0)
        select_bundesland(app)
        return select_landkreis(app)
    app.select_landkreis(landkreis)
    return landkreis


def select_city(app: AppAbfallplusDe.AppAbfallplusDe, bund_select: bool):
    cities = app.get_kommunen()
    questions = [
        inquirer.List(
            "city",
            choices=sorted([(s["name"], s["name"]) for s in cities])
            + ([("BACK", "BACK")] if bund_select else []),
            message="Select your Kommune",
        )
    ]
    city = inquirer.prompt(questions)["city"]
    if city == "BACK":
        app.clear(1)
        select_landkreis(app)
        return select_city(app, bund_select)

    app.select_kommune(city)
    return city


def select_bezirk(
    app: AppAbfallplusDe.AppAbfallplusDe, bund_select: bool
) -> Tuple[str, bool]:
    bezirke = app.get_bezirke()
    questions = [
        inquirer.List(
            "bezirk",
            choices=sorted([(s["name"], s["name"]) for s in bezirke])
            + [("BACK", "BACK")],
            message="Select your Bezirk",
        )
    ]
    bezirk = inquirer.prompt(questions)["bezirk"]
    if bezirk == "BACK":
        app.clear(2)
        select_city(app, bund_select)
        return select_bezirk(app, bund_select)

    return bezirk, app.select_bezirk(bezirk)


def select_street(app: AppAbfallplusDe.AppAbfallplusDe, bund_select: bool):
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
                choices=sorted([(s["name"], s["name"]) for s in streets])
                + [("BACK", "BACK")],
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

    app.select_street(street)
    return street


def select_house_number(app: AppAbfallplusDe.AppAbfallplusDe, bund_select: bool):
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
            choices=[(s, s) for s in sorted(AppAbfallplusDe.SUPPORTED_APPS)],
            message="Select your App",
        )
    ]
    app_id = inquirer.prompt(questions)["app-id"]

    app = AppAbfallplusDe.AppAbfallplusDe(app_id, "", "", "")
    bezirk_needed = "bezirk" in app.init_connection() and app.get_bezirke() != []
    cities = app.get_kommunen()
    bund_select = cities == []

    bundesland = landkreis = None
    if bund_select:
        bundesland = select_bundesland(app)
        landkreis = select_landkreis(app)
        # cities = app.get_kommunen()

    city = select_city(app, bund_select)
    finished = False
    house_number = ""
    street = None
    if bezirk_needed:
        bezirk, finished = select_bezirk(app, bund_select)
    if not finished:
        street = select_street(app, bund_select)
        if app.get_hrn_needed():
            house_number = select_house_number(app, bund_select)

    yaml = YAML["base"].format(
        app_id=app_id,
        city=city,
    )
    if bezirk_needed:
        yaml += YAML["bezirk"].format(bezirk=bezirk)
    if street:
        yaml += YAML["street"].format(strasse=street)
    if house_number:
        yaml += YAML["hnr"].format(hnr=house_number)
    if bundesland:
        yaml += YAML["bundesland"].format(bundesland=bundesland)
    if landkreis:
        yaml += YAML["landkreis"].format(landkreis=landkreis)

    print(yaml)


if __name__ == "__main__":
    main()
