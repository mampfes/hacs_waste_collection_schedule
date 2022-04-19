from unicodedata import name
import inquirer
import requests
import json

MUNICIPAL_CHOICES = [
    ("Moosburg", {"id": "20421", "name": "Moosburg"}),
    ("Pörtschach", {"id": "20424", "name": "Pörtschach"}),
    ("Techelsberg", {"id": "20435", "name": "Techelsberg"})
]

def prepareQuestionChoicesFromJsonText(text):
  jsonData = json.loads(text)

  addressEntries = []
  for entry in jsonData['address']:
      addressEntries.append(
        (entry['address']['name'], entry['address'])
      )

  return addressEntries

def main():
    # Municipal selection
    questions = [
        inquirer.List(
            "municipal", choices=MUNICIPAL_CHOICES, message="Select municipal (Gemeinde)"
        )
    ]
    answers = inquirer.prompt(questions)

    # Address selection
    r = requests.get(f"https://wsz-moosburg.at/api/address/{answers['municipal']['id']}")
    addressEntries = prepareQuestionChoicesFromJsonText(r.text)
    questions = [
        inquirer.List(
            "address", choices=addressEntries, message="Select address",
        )
    ]
    answers.update(inquirer.prompt(questions))

    # Some addresses have more streets, some have only 1 street, some have none.
    # Additional request only needed if at least one street will be there to select,
    # otherwise the final area ID is already returned in the address request.
    if int(answers['address']['sub']) > 0:
        r = requests.get(f"https://wsz-moosburg.at/api/address/{answers['municipal']['id']}/{answers['address']['id']}")
        streetEntries = prepareQuestionChoicesFromJsonText(r.text)
        questions = [
            inquirer.List(
                'street', choices=streetEntries, message='Select street',
            )
        ]
        answers.update(inquirer.prompt(questions))
    else:
        answers.update({'street': answers['address']})

    yamlComment = f"# ID for {answers['municipal']['name']} {answers['address']['name']} {answers['street']['name']}"

    print("Copy the following statements into your configuration.yaml:\n")
    print("# waste_collection_schedule source configuration")
    print("waste_collection_schedule:")
    print("  sources:")
    print("    - name: wsz-moosburg_at")
    print("      args:")
    print(f"        address_id: {answers['street']['id']} {yamlComment}")

if __name__ == "__main__":
    main()