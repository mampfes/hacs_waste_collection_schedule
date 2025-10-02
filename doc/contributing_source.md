<img src="/images/icon.png" alt="Waste Collection Schedule logo" title="Waste Collection Schedule" align="right" height="60" />

# Add support via a dedicated source

## Files required for a new Service Provider

The following files need to be provided to support a new service provider:

- A python `source script` that retrieves the collection schedule information, formats it appropriately, and has test cases that can be used to confirm functionality.
- A `source markdown (.md)` file that describes how to configure the new source and sensor, with examples.
- An updated `README.md` file containing details of the new service provider. This file will be automatically updated by a script.
- An updated `info.md` file containing details of the new service provider. This file will be automatically updated by a script.

The framework contains a [test script](#test-the-new-source-file) that can be used to confirm source scripts are retrieving and returning correctly formatted waste collection schedules.

## Python Source Script

Create a new file in the `/custom_components/waste_collection_schedule/waste_collection_schedule/source` folder. The file name should be the  url of your service provider in lower case, for example `abc_com.py` for `https://www.abc.com`.

The script should have the following general structure

```py
import datetime
from waste_collection_schedule import Collection

TITLE = "My Council" # Title will show up in README.md and info.md
DESCRIPTION = "Source script for abc.com"  # Describe your source
URL = "https://abc.com"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "TestName1": {"arg1": 100, "arg2": "street"},
    "TestName2": {"arg1": 200, "arg2": "road"},
    "TestName3": {"arg1": 300, "arg2": "lane"}
}

API_URL = "https://abc.com/search/"
ICON_MAP = {   # Optional: Dict of waste types and suitable mdi icons
    "DOMESTIC": "mdi:trash-can",
    "RECYCLE": "mdi:recycle",
    "ORGANIC": "mdi:leaf",
}

#### Arguments affecting the configuration GUI ####

HOW_TO_GET_ARGUMENTS_DESCRIPTION = { # Optional dictionary to describe how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages
    "en": "HOW TO GET ARGUMENTS DESCRIPTION",
    "de": "WIE MAN DIE ARGUMENTE ERHÄLT",
    "it": "COME OTTENERE GLI ARGOMENTI",
    "fr": "COMMENT OBTENIR LES ARGUMENTS",
}

PARAM_DESCRIPTIONS = { # Optional dict to describe the arguments, will be shown in the GUI configuration below the respective input field
    "en": {
        "arg1": "Description of ARG1",
        "arg2": "Description of ARG2",
    },
    "de": {
        "arg1": "Beschreibung von ARG1",
        "arg2": "Beschreibung von ARG2",
    },
    "it": {
        "arg1": "Descrizione di ARG1",
        "arg2": "Descrizione di ARG2",
    },
    "fr": {
        "arg1": "Description de ARG1",
        "arg2": "Description de ARG2",
    },
}

PARAM_TRANSLATIONS = { # Optional dict to translate the arguments, will be shown in the GUI configuration form as placeholder text
    "en": {
        "arg1": "User Readable Name for ARG1",
        "arg2": "User Readable Name for ARG2",
    },
    "de": {
        "arg1": "Benutzerfreundlicher Name für ARG1",
        "arg2": "Benutzerfreundlicher Name für ARG2",
    },
    "it": {
        "arg1": "Nome leggibile dall'utente per ARG1",
        "arg2": "Nome leggibile dall'utente per ARG2",
    },
    "fr": {
        "arg1": "Nom lisible par l'utilisateur pour ARG1",
        "arg2": "Nom lisible par l'utilisateur pour ARG2",
    },
}

#### End of arguments affecting the configuration GUI ####

class Source:
    def __init__(self, arg1:str, arg2:int):  # argX correspond to the args dict in the source configuration
        self._arg1 = arg1
        self._arg2 = arg2

    def fetch(self) -> list[Collection]:

        #  replace this comment with
        #  api calls or web scraping required
        #  to capture waste collection schedules
        #  and extract date and waste type details
        if ERROR_CONDITION:
            raise Exception("YOUR ERROR MESSAGE HERE") # DO NOT JUST return []

        entries = []  # List that holds collection schedule

        entries.append(
            Collection(
                date = datetime.datetime(2020, 4, 11),  # Collection date
                t = "Waste Type",  # Collection type
                icon = ICON_MAP.get("Waste Type"),  # Collection icon
            )
        )

        return entries
```

Filtering of data for waste types or time periods is a functionality of the framework and should not be done by the source script. Therefore:

- A source script should return all data for all available waste types.
- A source script should  **not** provide options to limit the returned waste types.
- A source script should return all data for the entire time period available (including past dates if they are returned).
- A source script should  **not** provide a configuration option to limit the requested time frame.

### Exceptions

- A source script should raise an exception if an error occurs during the fetch process. DO NOT JUST RETURN AN EMPTY LIST.
- A source should throw predefined exceptions wherever possible. You can import them from `waste_collection_schedule.exceptions`.:

| Exception | Description |
|-----------|-------------|
| `SourceArgumentExceptionMultiple` | Raised when there is an error with more than one argument, and you want the error to be displayed at specific arguments. |
| `SourceArgumentException` | Raised when there is an error with an argument and you want the error to be displayed at this argument. |
| `SourceArgumentSuggestionsExceptionBase` | Base class for exceptions that provide suggestions for arguments. |
| `SourceArgumentNotFound` | Raised when an argument could not be found by the API/during the fetch process. It should NOT be thrown when a required argument is not provided |
| `SourceArgumentNotFoundWithSuggestions` | As `SourceArgumentNotFound`, but with alternative suggestions. Preferred if you do know possible different values |
| `SourceArgAmbiguousWithSuggestions` | Raised when an argument leads to multiple matches and you do not know which to choose, should provide as many suggestions  as possible |
| `SourceArgumentRequired` | Raised when a required argument is missing. |
| `SourceArgumentRequiredWithSuggestions` | As `SourceArgumentRequired`, but with alternative suggestions. Preferred if you do know possible values |


## Service Provider Markdown File

Create a new markdown file in the `doc/source` folder. The file name should be the url of your service provider in lower case, for example `abc_com.md` for `https://www.abc.com`.

The markdown file should have the following general structure:

1. A description of how the source should be configured.
2. A description of the arguments required, the type, and whether they are optional/mandatory.
3. A working example (usually one of the test cases from the `.py` file)

For example:

**Configuration via configuration.yaml**

```yaml
waste_collection_schedule:
    sources:
    - name: abc_com
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

**Configuration Variables**

**uprn** _(string) (required)_ : The unique 12-digit identifier for your property

Example:

```yaml
waste_collection_schedule:
    sources:
    - name: abc_com
      args:
        uprn: "e3850cac2d5b"
```

Note: Your uprn can be found on invoices from your service provider

## Update Links in README.md and info.md

The `README.md` file in the top level folder contains a list of supported service providers.

The `info.md` is rendered in the HACS user interface within Home Assistant and gives potential users a summary of what the component does, and the service providers supported.

The links in both files can be updated automatically using the script `update_docu_links.py` in the top-level directory:

```bash
./update_docu_links.py
```

The script iterates through all source files and extracts some meta information like title and url. It is therefore important to set the attributes in the source file correctly. By default, the country classification is derived from the file name. If this doesn't match, the country code can be overwritten with the attribute `COUNTRY`.

| Attribute | Type | Description |
|-|-|-|
| TITLE | String | Title of the source. Used as link title in README.md and info.md. |
| URL | String | Service provider homepage URL. The idea is to help users to identify their service provider if they search for an URL instead of a service provider name. The abbreviated domain name is therefore displayed next to the source title in README.md. |
| COUNTRY | String | [Optional] Overwrite default country code which is derived from source file name. |
| EXTRA_INFO | List of Dicts or Callable | [Optional] Used to add extra links in README.md and info.md if the source supports multiple service providers at the same time. The following keys can be added to the dict: `title`, `url`, `country`, `default_params`. In case a key (`title`, `url`, `country`) is missing, the corresponding value from the attributes above will be used instead. The `default_params` is a dictionary that will be auto filled when selecting this extra_info provider in the GUI configuration form. |
| HOW_TO_GET_ARGUMENTS_DESCRIPTION | Dict | [Optional] Description of how to get the arguments, will be shown in the GUI configuration form above the input fields, does not need to be translated in all languages. |
| PARAM_DESCRIPTIONS | Dict | [Optional] Description of the arguments, will be shown in the GUI configuration below the respective input field. |
| PARAM_TRANSLATIONS | Dict | [Optional] Translate the arguments, will be shown in the GUI configuration form as placeholder text. Some common parameters will be automatically translated if you do not provide this |

Examples:

```python
# Standard case: Source supports one service provider
TITLE = "ART Trier"
URL = "https://www.art-trier.de"

# Special case: Overwrite country code
TITLE = "RecycleSmart"
URL = "https://www.recyclesmart.com/"
COUNTRY = "au"

# Special case: Source supports multiple service provider which should be added to README.md and info.md
TITLE = "FCC Environment"
URL = "https://fccenvironment.co.uk"
EXTRA_INFO = [
    {
        "title": "Harborough District Council",
        "url": "https://harborough.gov.uk",
        "default_params": { # optional will be auto filled when selecting in the GUI configuration form
            "ARG1": "Harborough",
        }
    },
    {
        "title": "South Hams District Council",
        "url": "https://southhams.gov.uk/",
        "default_params": { # optional will be auto filled when selecting in the GUI configuration form
            "ARG1": "South Hams",
        }
    },
]

# Special case: Same as before, but EXTRA_INFO created by a function from existing data
TITLE = "Bürgerportal"
URL = "https://www.c-trace.de"
def EXTRA_INFO():
    return [ { "title": s["title"], "url": s["url"] } for s in SERVICE_MAP ] # may also contain the default_params key (see above)
```

## Test the new Source File

Debugging a source script within Home Assistant is not recommended. Home Assistant's start-up process is too slow for fast debugging cycles. To help with debugging/troubleshooting, the Waste Collection Schedule framework contains a command line script that can be used to test source scripts. The script iterates through the `test cases` defined in the source script passing each set of arguments to the source script and prints the results.

The script supports the following options:

| Option | Argument | Description                                                                                                                                     |
|--------|----------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| `-s`   | SOURCE   | [Source name](https://github.com/mampfes/hacs_waste_collection_schedule#source-configuration-variables) (source file name without ending `.py`) |
| `-l`   | -        | List all found dates. |
| `-i`   | -        | Add icon name to output. Only effective together with `-l`. |
| `-t`   | -        | Show extended exception info and stack trace. |
| `-d`   | -        | Runs the fetch method twice and checks if the resulsts differ, should be used if the fetch method modifies the Source object. |

For debugging purposes of a single source, it is recommended to use the `-s SOURCE` option. If used without any arguments provided, the script tests every script in the `/custom_components/waste_collection_schedule/waste_collection_schedule/source` folder and all yaml configurations in the folder `/doc/ics/yaml` and prints the number of found entries for every test case.

To use it:

1. Navigate to the `/custom_components/waste_collection_schedule/waste_collection_schedule/test/` directory
2. Confirm the `test_sources.py` script is present
3. Execute the test script. For example, testing the abfall_io.py source script would be:

   ```bash
   test_sources.py -s abfall_io
   ```

4. Confirm the results returned match expectation. For example, testing abfall_io returns:

   ```text
   Testing source abfall_io ...
     found 285 entries for Waldenbuch
     found 58 entries for Landshut
     found 109 entries for Schoenmackers
     found 3 entries for Freudenstadt
     found 211 entries for Ludwigshafen am Rhein
     found 119 entries for Traunstein
     found 287 entries for Thalheim
   ```

5. To view individual date entries and assigned icons, use the `-i -l` arguments, for example:

   ```bash
   test_sources.py -s richmondshire_gov_uk -i -l
   Testing source richmondshire_gov_uk ...
     found 53 entries for test 1
       2023-01-02: 240L GREY RUBBISH BIN [mdi:trash-can]
       2023-01-07: 55L RECYCLING BOX [mdi:recycle]
       2023-01-13: 240L GREY RUBBISH BIN [mdi:trash-can]
       2023-01-20: 55L RECYCLING BOX [mdi:recycle]
       2023-01-27: 240L GREY RUBBISH BIN [mdi:trash-can]
       ...
       2023-12-01: 240L GREY RUBBISH BIN [mdi:trash-can]
       2023-12-08: 55L RECYCLING BOX [mdi:recycle]
       2023-12-15: 240L GREY RUBBISH BIN [mdi:trash-can]
   ```

### Test before submitting using pytest

To ensure that the source script is working as expected, it is recommended to install and run `pytest` in the `waste_collection_schedule` directory. This will run some additional tests making sure attributes are set correctly and all required files are present and update_docu_links run successfully. Pytest does not test the source script itself.
