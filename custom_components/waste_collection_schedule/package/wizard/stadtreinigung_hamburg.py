#!/usr/bin/python3

import inquirer
import requests
import json
from html.parser import HTMLParser


# Parser for HTML option list
class OptionParser(HTMLParser):
    def __init__(self, select_name):
        super().__init__()
        self._select_name = select_name
        self._within_select = False
        self._within_option = False
        self._option_name = ""
        self._option_value = "-1"
        self._choices = []

    @property
    def choices(self):
        return self._choices

    def handle_starttag(self, tag, attrs):
        if tag == "select":
            for attr in attrs:
                if attr[0] == "name" and attr[1] == self._select_name:
                    self._within_select = True
                    break
        elif tag == "option" and self._within_select:
            self._within_option = True
            for attr in attrs:
                if attr[0] == "value":
                    self._option_value = attr[1]

    def handle_endtag(self, tag):
        if tag == "select":
            self._within_select = False
        elif tag == "option":
            if (
                self._within_select
                and self._within_option
                and len(self._option_name) > 0
                and self._option_value != ""
            ):
                self._choices.append((self._option_name, self._option_value))
            self._within_option = False
            self._option_name = ""
            self._option_value = "-1"

    def handle_data(self, data):
        if self._within_option:
            self._option_name += data


def main():
    # search for street
    questions = [
        inquirer.Text("strasse", message="Enter search string for street name"),
        #        inquirer.Text("hausnummer", message="Enter search string for building number"),
    ]
    answers = inquirer.prompt(questions)

    args = answers
    args["hausnummer"] = ""
    args["bestaetigung"] = "true"
    args["mode"] = "search"

    r = requests.post(
        "https://www.stadtreinigung.hamburg/privatkunden/abfuhrkalender/index.html",
        data=args,
    )

    # parser HTML option list
    parser = OptionParser(select_name="asId")
    parser.feed(r.text)

    questions = [inquirer.List("asId", choices=parser.choices, message="Select street")]
    answers = inquirer.prompt(questions)

    # search for building number
    args = answers.copy()
    args["hausnummer"] = ""
    args["bestaetigung"] = "true"
    args["mode"] = "search"

    r = requests.post(
        "https://www.stadtreinigung.hamburg/privatkunden/abfuhrkalender/index.html",
        data=args,
    )

    # parser HTML option list
    parser = OptionParser(select_name="hnId")
    parser.feed(r.text)

    questions = [
        inquirer.List("hnId", choices=parser.choices, message="Select house number")
    ]
    answers.update(inquirer.prompt(questions))

    print("Copy the following statements into your configuration.yaml:\n")
    print("# waste_collection_schedule source configuration")
    print("waste_collection_schedule:")
    print("  sources:")
    print("    - name: stadtreinigung_hamburg")
    print("      args:")
    print(f"        asId: {answers['asId']}")
    print(f"        hnId: {answers['hnId']}")


if __name__ == "__main__":
    main()
