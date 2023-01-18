#!/usr/bin/env python3

import re
import site
from html.parser import HTMLParser
from pathlib import Path

import inquirer
import requests

# add module directory to path
package_dir = Path(__file__).resolve().parents[2]
site.addsitedir(str(package_dir))
from waste_collection_schedule.service.AbfallIO import SERVICE_MAP  # type: ignore # isort:skip # noqa: E402


MODUS_KEY = "d6c5855a62cf32a4dadbc2831f0f295f"
HEADERS = {"user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}

# IDs of CONFIG VARIABLES
CONFIG_VARIABLES = [
    "f_id_kommune",
    "f_id_bezirk",
    "f_id_strasse",
    "f_id_strasse_hnr",
    "f_abfallarten",
]

ACTION_EXTRACTOR_PATTERN = re.compile(
    '(?<=awk-data-onchange-submit-waction=")[^\\n\\r"]+'
)


class OptionParser(HTMLParser):
    """Parser for HTML option list."""

    TEXTBOXES = "textboxes"

    def error(self, message):
        pass

    def __init__(self, target_var):
        super().__init__()
        self._target_var = target_var
        self._within_option = False
        self._option_name = ""
        self._option_value = "-1"
        self._choices = []
        self._is_selector = False
        self._is_text_input = False
        self._text_field_id = ""
        self._text_hint = ""
        self._text_name = ""
        self._label_for_id = ""
        self._label_contents = {}

    @property
    def choices(self):
        return self._choices

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)

        if tag == "label":
            if "for" in attributes:
                self._label_for_id = attributes["for"]

        if tag == "input":
            if "type" in attributes:
                if attributes["type"] == "hidden":
                    if (
                        "name" in attributes
                        and "value" in attributes
                        and attributes["name"] == self._target_var
                    ):
                        # self._within_option = True
                        self._is_selector = True
                        self._option_value = attributes["value"]
                        self._choices.append((attributes["value"], attributes["value"]))
                elif (
                    self._target_var == OptionParser.TEXTBOXES
                    and attributes["type"] == "text"
                ):
                    self._is_text_input = True
                    if "id" in attributes:
                        self._text_field_id = attributes["id"]
                    if "placeholder" in attributes:
                        self._text_hint = attributes["placeholder"]
                    if "name" in attributes:
                        self._text_name = attributes["name"]

        if tag == "select":
            if "name" in attributes and attributes["name"] == self._target_var:
                self._is_selector = True

        if tag == "option" and self._is_selector:
            self._within_option = True
            if "value" in attributes:
                self._option_value = attributes["value"]

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

        if len(self._label_for_id) > 0:
            self._label_contents[self._label_for_id] = data
            self._label_for_id = ""

    @property
    def is_selector(self):
        return self._is_selector

    @property
    def is_text_input(self):
        return self._is_text_input

    @property
    def text_name(self):
        return self._text_name

    @property
    def text_field_id(self):
        return self._text_field_id

    @property
    def label_contents(self):
        return self._label_contents

    @property
    def text_hint(self):
        return self._text_hint


def select_and_query(data, answers):
    relevant_config_vars = []
    for config_var in CONFIG_VARIABLES:
        if config_var not in answers and config_var in data:
            relevant_config_vars.append(config_var)

    for target_var in relevant_config_vars:
        # parser HTML option list
        parser = OptionParser(target_var)
        parser.feed(data)

        if parser.is_selector:
            questions = [
                inquirer.List(
                    target_var,
                    choices=parser.choices,
                    message=f"Select {target_var}",
                )
            ]
            answers.update(inquirer.prompt(questions))

    # Search for Textboxes (currently just supports one textbox per request)
    parser = OptionParser(OptionParser.TEXTBOXES)
    parser.feed(data)
    if parser.is_text_input:
        message = parser.label_contents[parser.text_field_id]
        if parser.text_hint != "":
            message = message + " (" + parser.text_hint + ")"

        questions = [inquirer.Text(parser.text_name, message=message)]
        answers.update(inquirer.prompt(questions))

    args = {
        "key": answers["key"],
        "modus": MODUS_KEY,
        "waction": ACTION_EXTRACTOR_PATTERN.findall(data)[0],
    }
    r = requests.post(
        "https://api.abfall.io", params=args, data=answers, headers=HEADERS
    )
    return r.text


def main():
    questions = [
        inquirer.List(
            "key",
            choices=[(s["title"], s["service_id"]) for s in SERVICE_MAP],
            message="Select service provider",
        )
    ]
    answers = inquirer.prompt(questions)

    # prompt for first level
    args = {"key": answers["key"], "modus": MODUS_KEY, "waction": "init"}
    r = requests.get("https://api.abfall.io", params=args, headers=HEADERS)

    data = r.text
    while True:
        data = select_and_query(data, answers)

        if "f_id_abfalltyp" in data:
            break

    print("Copy the following statements into your configuration.yaml:\n")
    print("# waste_collection_schedule source configuration")
    print("waste_collection_schedule:")
    print("  sources:")
    print("    - name: abfall_io")
    print("      args:")
    for key, value in answers.items():
        if key in CONFIG_VARIABLES or key == "key":
            print(f"        {key}: {value}")


if __name__ == "__main__":
    main()
