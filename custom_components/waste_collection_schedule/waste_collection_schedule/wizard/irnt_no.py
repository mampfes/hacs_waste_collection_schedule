#!/usr/bin/env python3

import urllib.parse

import inquirer
import requests

URL_ADDRESS_SEARCH = "https://innherredrenovasjon.no/wp-json/ir/v1/addresses/{search}"


def main():
    # search for address
    while True:
        questions = [inquirer.Text("search", message="Enter search string for address")]
        answers = inquirer.prompt(questions)

        # retrieve suggestions for address
        response = requests.get(
            URL_ADDRESS_SEARCH.format(search=urllib.parse.quote(answers["search"])),
            headers={
                "User-Agent": "Mozilla/5.0",
                "Cache-Control": "max-age=0",
            },
        ).json()
        data = response["data"]
        if len(data["results"]) == 0:
            print("Search returned no result. Please try again.")
        else:
            break

    addresses = dict((item["id"], item) for item in data["results"])

    # select address
    addresses_list = [
        (f"{v['address']} ({v['municipality']})", k) for k, v in addresses.items()
    ]
    questions = [
        inquirer.List("premise_id", choices=addresses_list, message="Select address")
    ]
    args = inquirer.prompt(questions)

    print("Copy the following statements into your configuration.yaml:\n")
    print("# waste_collection_schedule source configuration")
    print("waste_collection_schedule:")
    print("  sources:")
    print("    - name: irnt_no")
    print("      args:")
    for key, value in args.items():
        print(f"        {key}: {value}")

    # Add address details as comments
    address_details = addresses.get(args["premise_id"])
    print(
        "\n".join(
            [
                f"        # {k}: {v}"
                for k, v in address_details.items()
                if k not in ["id"]
            ]
        )
    )


if __name__ == "__main__":
    main()
