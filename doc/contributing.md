<img src="/images/icon.png" alt="Waste Collection Schedule logo" title="Waste Collection Schedule" align="right" height="60" />

# Contributing To Waste Collection Schedule

![python badge](https://img.shields.io/badge/Made%20with-Python-orange)
![github contributors](https://img.shields.io/github/contributors/mampfes/hacs_waste_collection_schedule?color=orange)
![last commit](https://img.shields.io/github/last-commit/mampfes/hacs_waste_collection_schedule?color=orange)

There are several ways of contributing to this project, including:

- Providing new service providers
- Updating or improving the documentation
- Helping answer/fix any issues raised
- Join in with the Home Assistant Community discussion

## Adding New Service Providers

### Fork And Clone The Repository, And Checkout A New Branch

In GitHub, navigate to the repository [homepage](https://github.com/mampfes/hacs_waste_collection_schedule). Click the `fork` button at the top-right side of the page to fork the repository.

![fork](/images/wcs_fork_btn.png)

Navigate to your fork's homepage, click the `code` button and copy the url.

![code](/images/wcs_code_btn.png)

On your local machine, open a terminal and navigate to the location where you want the cloned directory. Type `git clone` and paste in the url copied earlier. It should look something like this, but with your username replacing `YOUR-GITHUB-USERNAME`:

```bash
git clone https://github.com/YOUR-GITHUB-USERNAME/hacs_waste_collection_schedule
```

Before making any changes, create a new branch to work on.

```bash
git branch <new_branch_name>
```

For example, if you were adding a new provider called abc.com, you could do

```bash
git branch adding_abc_com
```

For more info on forking/cloning a repository, see GitHub's [fork-a-repo](https://docs.github.com/en/get-started/quickstart/fork-a-repo) document.

### Files Required For A New Service Provider

The following files need to be provided to support a new service provider:

- A python `source script` that retrieves the collection schedule information, formats it appropriately, and has test cases that can be used to confirm functionality.
- A `source markdown (.md)` file that describes how to configure the new source and sensor, with examples.
- An updated `README.md` file containing details of the new service provider.
- An updated `info.md` file containing details of the new service provider.

The framework contains a [test script](#test-the-new-source-file) that can be used to confirm source scripts are retrieving and returning correctly formatted waste collection schedules.

### Python Source Script

Create a new file in the `custom_components/waste_collection_schedule/waste_collection_schedule/source` folder. The file name should be the  url of your service provider in lower case, for example `abc_com.py` for `https://www.abc.com`.

The script should have the following general structure

```py
import datetime
from waste_collection_schedule import Collection

TITLE = "My Council" # Title will show up in README.md and info.md
DESCRIPTION = "Source script for abc.com"  # Describe your source
URL = "https://abc.com"  # Insert url to service homepage. URL will show up in README.md and info.md
TEST_CASES = {  # Insert arguments for test cases to be used by test_sources.py script
    "TestName1": {"arg1": 100, "arg2": "street"}
    "TestName2": {"arg1": 200, "arg2": "road"}
    "TestName3": {"arg1": 300, "arg2": "lane"}
}

API_URL = "https://abc.com/search/"
ICON_MAP = {   # Optional: Dict of waste types and suitable mdi icons
    "DOMESTIC": "mdi:trash-can",
    "RECYCLE": "mdi:recycle",
    "ORGANIC": "mdi:leaf",
}


class Source:
    def __init__(self, arg1, arg2):  # argX correspond to the args dict in the source configuration
        self._arg1 = arg1
        self._arg2 = arg2

    def fetch(self):

        #  replace this comment with
        #  api calls or web scraping required
        #  to capture waste collection schedules
        #  and extract date and waste type details

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

### Service Provider Markdown File

Create a new markdown file in the `custom_components/waste_collection_schedule/doc/source` folder. The file name should be the  url of your service provider in lower case, for example `abc_com.md` for `https://www.abc.com`.

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

### Update Links in README.md and info.md

The `README.md` file in the top level folder contains a list of supported service providers.

The `info.md` is rendered in the HACS user interface within Home Assistant and gives potential users a summary of what the component does, and the service providers supported.

The links in both files can be updated automatically using the script `update_docu_links.py` in the top-level directory:

```bash
./make_docu_links.py
```

The script iterates through all source files and extracts some meta information like title and url. It is therefore important to set the attributes in the source file correctly. By default, the country classification is derived from the file name. If this doesn't match, the country code can be overwritten with the attribute `COUNTRY`.

| Attribute | Type | Description |
|-|-|-|
| TITLE | String | Title of the source. Used as link title in README.md and info.md. |
| URL | String | Service provider homepage URL. The idea is to help users to identify their service provider if they search for an URL instead of a service provider name. The abbreviated domain name is therefore displayed next to the source title in README.md. |
| COUNTRY | String | [Optional] Overwrite default country code which is derived from source file name. |
| EXTRA_INFO | List of Dicts or Callable | [Optional] Used to add extra links in README.md and info.md if the source supports multiple service providers at the same time. The following keys can be added to the dict: `title`, `url`, `country`. In case a key is missing, the corresponding value from the attributes above will be used instead. |

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
       "url": "https://harborough.gov.uk"
    },
    {
       "title": "South Hams District Council",
       "url": "https://southhams.gov.uk/"
    },
]

# Special case: Same as before, but EXTRA_INFO created by a function from existing data
TITLE = "Bürgerportal"
URL = "https://www.c-trace.de"
def EXTRA_INFO():
    return [ { "title": s["title"], "url": s["url"] } for s in SERVICE_MAP ]
```

### Test The New Source File

Debugging a source script within Home Assistant is not recommended. Home Assistant's start-up process is too slow for fast debugging cycles. To help with debugging/troubleshooting, the Waste Collection Schedule framework contains a command line script that can be used to test source scripts. The script iterates through the `test cases` defined in the source script passing each set of arguments to the source script and prints the results.

The script supports the following options:

| Option | Argument | Description                                                                                                                                     |
|--------|----------|-------------------------------------------------------------------------------------------------------------------------------------------------|
| `-s`   | SOURCE   | [Source name](https://github.com/mampfes/hacs_waste_collection_schedule#source-configuration-variables) (source file name without ending `.py`) |
| `-l`   | -        | List all found dates. |
| `-i`   | -        | Add icon name to output. Only effective together with `-l`. |

For debugging purposes of a single source, it is recommended to use the `-s SOURCE` option. If used without any arguments provided, the script tests every script in the `custom_components/waste_collection_schedule/waste_collection_schedule/source` folder and prints the number of found entries for every test case.

To use it:

1. Navigate to the `custom_components/waste_collection_schedule/waste_collection_schedule/test/` directory
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

### Sync Branch and Create A Pull Request

Having completed your changes, sync your local branch to your GitHub repo, and then create a pull request. When creating a pull request, please provide a meaningful description of what the pull request covers. Ideally it should cite the service provider, confirm the .py, .md, README and info.md files have all been updated, and the output of the test_sources.py script demonstrating functionality. Once submitted a number of automated tests are run against the updated files to confirm they can be merged into the master branch. Note: Pull requests from first time contributors also undergo a manual code review before a merge confirmation in indicated.

Once a pull request has been merged into the master branch, you'll receive a confirmation message. At that point you can delete your branch if you wish.

## Update Or Improve The Documentation

Non-code contributions are welcome. If you find typos, spelling mistakes, or think there are other ways to improve the documentation please submit a pull request with updated text. Sometimes a picture paints a thousand words, so if a screenshots would better explain something, those are also welcome.

## Help Answer/Fix Issues Raised

![GitHub issues](https://img.shields.io/github/issues-raw/mampfes/hacs_waste_collection_schedule?color=orange)

Open-source projects are always a work in progress, and [issues](https://github.com/mampfes/hacs_waste_collection_schedule/issues) arise from time-to-time. If you come across a new issue, please raise it. If you have a solution to an open issue, please raise a pull request with your solution.

## Join The Home Assistant Community Discussion

![Community Discussion](https://img.shields.io/badge/Home%20Assistant%20Community-Discussion-orange)

The main discussion thread on Home Assistant's Community forum can be found [here](https://community.home-assistant.io/t/waste-collection-schedule-framework/186492).
