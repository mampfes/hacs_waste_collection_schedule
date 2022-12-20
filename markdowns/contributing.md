# Contributing to Waste Collection Schedule

There are ??? ways of contributing to this custom component, they are:
- Provide new service providers
- Update or improve the documentation
- Help answer/fix issues raised


## Adding New Service Providers

### Clone the repository
Clone the `Waste Collection Schedule` repository and check out a new branch for your updates.

The following files need to be provided to support a new service provider:
- A python `source script` that retrieves the collection schedule information, formats it appropriately, and has test cases that can be used to confirm functionallty. The framework contains a test script to facilitate debugguing/troubleshooting and correctly formatted waste collection schedules are being returned.
- A `source markdown (.md)` file that describes how to configure the new source and sensor, with examples
- An updated `README.md` file containing details of the new service provider
- An updated `info.md` file containing details of the new service provider
The framework contains a test script that can be used to confirm source scripts are retrieving and returning correctly formatted waste collection schedules.

### Python source script

Create a new file in the `custom_components/waste_collection_schedule/waste_collection_schedule/source` folder. The file name should be the  url of your service provider in lower case, for example `abc_com.py` for `https://www.abc.com`.

The script should have the following general structure

```py
import datetime
from waste_collection_schedule import Collection


DESCRIPTION = "Example source for abc.com"  # Describe your source
URL = "abc.com"  # Insert url to service homepage
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "TestName1": {"arg1": 100, "arg2": "street"}
    "TestName2": {"arg1": 200, "arg2": "road"}
    "TestName3": {"arg1": 300, "arg2": "lane"}
}
API_URLS = { # Dict of API end-points if used
    "address_search": "https://abc.com/search/",
    "collection": "https://abc.com/search/{}/",
}
ICONS = {   # Dict of waste types and suitable mdi icons
    "DOMESTIC": "mdi:trash-can",
    "RECYCLE": "mdi:recycle",
    "ORGANIC": "mdi:leaf",
}


class Source:
    def __init__(self, arg1, arg2):  # argX correspond to the args dict in the source configuration
        self._arg1 = arg1
        self._arg2 = arg2

    def fetch(self):

        #  commands using api end-points and self._argX
        #  to capture waste collection schedules
        #  and extract date and waste type details

        entries = []  # List that holds collection schedule

        entries.append(
            Collection(
                date = datetime.datetime(2020, 4, 11),  # Collection date
                t = "Waste Type",  # Cellection type
                icon = ICONS.get("Waste Type"),  # Collection icon
            )
        )

        return entries
```
Filtering of data for waste types or time periods is a functionality of the framework and should not be done by the source script. Therefore:
- A source script should return data for all available waste types.
- A source script should  **not** provide options to limit the returned waste types.
- A source script should return data for the entire time period available (including past dates if they are returned).
- A source script should  **not** provide a configuration option to limit the requested time frame.


### Markdown file
Create a new markdown file in the `custom_components/waste_collection_schedule/doc/source` folder. The file name should be the  url of your service provider in lower case, for example `abc_com.md` for `https://www.abc.com`.



### Updated README.md file
The README.md file in the top level folder contains a list of supported service providers. Please add your new entry to the relevant country section, creating a new section if yours is the first provider for that country. The entry should contain the name of the service provider and a link to the service providers markdown file. For example:
```markdown
- [Abfall.IO / AbfallPlus.de](./doc/source/abfall_io.md)
```

### Updated info.md file


### Test the new source file
Debugging a source script within Home Assistant is not recommended. Home Assistant's start-up process is too slow for fast debugging cycles. To help with debugging/troubleshooting, the Waste Collection Schedule framework contains a command line script that can be used to test source sctipts. The script iterates throught the `test cases` defined in the source script passing each set of arguements to the source script and prints the results.

The script supports the following options:

| Option | Argument | Description                                                                                                                                     |
|--------|----------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| `-s`   | SOURCE   | [Source name](https://github.com/mampfes/hacs_waste_collection_schedule#source-configuration-variables) (source file name without ending `.py`) |
| `-l`   | -        | List all found dates                                                                                                                            |
| `-i`   | -        | Add icon name to output. Only effective together with `-l`.                                                                                     |

For debugging purposes of a single source, it is recommended to use the `-s SOURCE` option. If used without any arguments provided, the script tests every script in the `custom_components/waste_collection_schedule/waste_collection_schedule/source` folder and prints the number of found entries for every test case.

To use it:
1. Navigate to the `custom_components/waste_collection_schedule/waste_collection_schedule/test/` directory
2. Confirm the `test_sources.py` script is present
3. Execute the test script. For example, testing the abfall_io.py source script would be:
```bash
test_sources.py -s abfall_io -l -i
```
4. Confirm the results returned match expectation. For example, testing abfall_io returns:
```text
Testing source abfall_io ...
  found 269 entries for Waldenbuch
  found 55 entries for Landshut
  found 101 entries for Schoenmackers
  found 139 entries for Freudenstadt
  found 190 entries for Ludwigshafen am Rhein
```

### Create a pull request


See also: [custom_components/waste_collection_schedule/waste_collection_schedule/source/example.py](./custom_components/waste_collection_schedule/waste_collection_schedule/source/example.py)

