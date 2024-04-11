"""
Generates a new json source file for testing purposes.

Script can be used to generate a new ukbcd_test.json file if the dates in the current version elapse.
Randomly generates 4 waste collections per month for the next 5 years.
Before running, check they haven't changed the json structure: https://github.com/robbrad/UKBinCollectionData
"""

import datetime
import json
from pathlib import Path
from random import choice, randint

ROOT_DIR = Path(__file__).parents[1]
TEST_DIR = ROOT_DIR / "test"
FILENAME = "test_ukbcd.json"
WASTES = ["Refuse", "Recycling", "Garden", "Food", "Paper & Cardboard", "Batteries"]

data: dict = {"bins": []}
year = datetime.date.today().year
for year in range(year, year + 6):
    for month in range(1, 13):
        for days in range(0, 4):
            day = randint(1, 28)
            dt = f"{day:02d}" + "/" + f"{month:02d}" + "/" + f"{year:04d}"
            dict_data = {"type": choice(WASTES), "collectionDate": dt}
            data["bins"].append(dict_data)
json_object = json.dumps(data, ensure_ascii=False, indent=4)

with open(Path(TEST_DIR / FILENAME), "w") as outfile:
    outfile.write(json_object)
