import json
from datetime import datetime
from pathlib import Path

from waste_collection_schedule import Collection  # type: ignore[attr-defined]

TITLE = "UK Bin Collection Schedule (UKBCD) project"
DESCRIPTION = "Source for json-based schedules generated by UKBCD project scripts."
URL = None
COUNTRY = "uk"
ROOT_DIR = Path(__file__).parents[1]
TEST_FILE = ROOT_DIR / "test" / "test_ukbcd.json"
TEST_CASES = {
    "Test_File": {
        # Path is used here to allow the Source call from any location. It is not required in a yaml configuration.
        "file": str(Path(TEST_FILE))
    }
}


class Source:
    def __init__(self, file=None):
        self._file = file

    def fetch(self):
        if self._file is not None:
            json_file = open(self._file)
            schedule = json.load(json_file)["bins"]
            entries = []
            for item in schedule:
                entries.append(
                    Collection(
                        date=datetime.strptime(
                            item["collectionDate"], "%d/%m/%Y"
                        ).date(),
                        t=item["type"],
                    )
                )
        else:
            raise RuntimeError("Unable to find file, check config path and file name")

        return entries


"""
If the test case returns no entries, check dates in the source file are not all in the past.
If they are, a new test_ukbcd.json file with future dates can be generated using service script located at:
custom_components/waste_collection_schedule/waste_collection_schedule/service/generate_ukbcd_json.py
"""
