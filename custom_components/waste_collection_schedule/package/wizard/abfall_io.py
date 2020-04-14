#!/usr/bin/python3

import inquirer
import requests
import json  # TODO: remove
from html.parser import HTMLParser

MODUS_KEY = "d6c5855a62cf32a4dadbc2831f0f295f"

# Parser for HTML option list
class OptionParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self._within_option = False
        self._option_name = ""
        self._option_value = "-1"
        self._choices = []
        self._select_name = ""

    @property
    def choices(self):
        return self._choices

    @property
    def select_name(self):
        return self._select_name

    def handle_starttag(self, tag, attrs):
        if tag == "option":
            self._within_option = True
            for attr in attrs:
                if attr[0] == "value":
                    self._option_value = attr[1]
        elif tag == "select":
            for attr in attrs:
                if attr[0] == "name":
                    self._select_name = attr[1]

    def handle_endtag(self, tag):
        if (
            self._within_option
            and len(self._option_name) > 0
            and self._option_value != "-1"
        ):
            self._choices.append((self._option_name, self._option_value))
        self._within_option = False
        self._option_name = ""
        self._option_value = "-1"

    def handle_data(self, data):
        if self._within_option:
            self._option_name += data


def main():
    # select district
    district_choices = [
        ("Böblingen", "8215c62763967916979e0e8566b6172e"),
        ("Kitzingen", "594f805eb33677ad5bc645aeeeaf2623"),
        ("Göppingen", "365d791b58c7e39b20bb8f167bd33981"),
        ("Landsberg am Lech", "7df877d4f0e63decfb4d11686c54c5d6"),
        ("Landshut", "bd0c2d0177a0849a905cded5cb734a6f"),
        ("Rotenburg (Wümme)", "645adb3c27370a61f7eabbb2039de4f1"),
        ("Sigmaringen", "39886c5699d14e040063c0142cd0740b"),
        ("MüllALARM / Schönmackers", "e5543a3e190cb8d91c645660ad60965f"),
        ("Unterallgäu", "c22b850ea4eff207a273e46847e417c5"),
        ("Westerwaldkreis", "248deacbb49b06e868d29cb53c8ef034"),
    ]
    questions = [
        inquirer.List(
            "key",
            choices=district_choices,
            message="Bitte wählen Sie zuerst den gewünschten Ort/Landkreis aus",
        )
    ]
    answers = inquirer.prompt(questions)

    # prompt for city
    args = {"key": answers["key"], "modus": MODUS_KEY, "waction": "init"}
    r = requests.get(f"https://api.abfall.io", params=args)

    # parser HTML option list
    parser = OptionParser()
    parser.feed(r.text)

    questions = [
        inquirer.List(
            "f_id_kommune",
            choices=parser.choices,
            message="Bitte wählen Sie zuerst den gewünschten Ort aus",
        )
    ]
    answers.update(inquirer.prompt(questions))

    # prompt for next level under kommune, returns district or street!!!
    args = {"key": answers["key"], "modus": MODUS_KEY, "waction": "auswahl_kommune_set"}
    data = {
        "f_id_kommune": answers["f_id_kommune"],
    }
    r = requests.post(f"https://api.abfall.io", params=args, data=data)

    # parser HTML option list
    parser = OptionParser()
    parser.feed(r.text)

    if parser.select_name == "f_id_bezirk":
        # last query returned list of districts, therefore query districts first
        questions = [
                inquirer.List(
                    "f_id_bezirk",
                    choices=parser.choices,
                    message="Bitte wählen Sie den gewünschten Bezirk aus",
                )
            ]
        answers.update(inquirer.prompt(questions))
        args = {"key": answers["key"], "modus": MODUS_KEY, "waction": "auswahl_bezirk_set"}
        data = {
            "f_id_kommune": answers["f_id_kommune"],
            "f_id_bezirk": answers["f_id_bezirk"],
        }
        r = requests.post(f"https://api.abfall.io", params=args, data=data)

        # parser HTML option list
        parser = OptionParser()
        parser.feed(r.text)
    
    if parser.select_name != "f_id_strasse":
        print(f"missing query for {parser.select_name}")
        return

    questions = [
        inquirer.List(
            "f_id_strasse",
            choices=parser.choices,
            message="Bitte wählen Sie die gewünschte Strasse aus",
        )
    ]
    answers.update(inquirer.prompt(questions))

    print("Copy the following statements into your configuration.yaml:\n")
    print("# waste_collection_schedule source configuration")
    print("waste_collection_schedule:")
    print("  sources:")
    print("    - name: abfall_io")
    print("      args:")
    print(f"        key: {answers['key']}")
    print(f"        f_id_kommune: {answers['f_id_kommune']}")
    if "f_id_bezirk" in answers:
        print(f"        f_id_bezirk: {answers['f_id_bezirk']}")
    print(f"        f_id_strasse: {answers['f_id_strasse']}")


if __name__ == "__main__":
    main()
