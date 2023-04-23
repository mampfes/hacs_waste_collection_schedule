<img src="/images/icon.png" alt="Waste Collection Schedule logo" title="Waste Collection Schedule" align="right" height="60" />

# Add support via generic ICS source

## Files required for a new Service Provider

The following files need to be provided to support a new service provider:

- A `yaml based ICS configuration` file that contains the name and the url of the supported service provider and has test cases that can be used to confirm functionality.
- A `source markdown (.md)` file that describes how to configure the new source and sensor, with examples. This file will be generated automatically out of the yaml file 
- An updated `README.md` file containing details of the new service provider. This file will be automatically updated by a script.
- An updated `info.md` file containing details of the new service provider. This file will be automatically updated by a script.

The framework contains a [test script](#test-the-new-source-file) that can be used to confirm source scripts are retrieving and returning correctly formatted waste collection schedules.

## yaml based ICS configuration

Create a new file in the `/doc/ics/yaml` folder. The file name should be the url of your service provider in lower case, for example `abc_com.yaml` for `https://www.abc.com`.

The yaml file should have the following general structure

```yaml
title: TITLE
url: URL
country: COUNTRY
howto: HOWTO
test_cases: TEST_CASES
```

| Attribute | Type | Description |
|-|-|-|
| title | String | Title of the service provider. Used as link title in README.md and info.md. |
| url | String | Service provider homepage URL. The idea is to help users to identify their service provider if they search for an URL instead of a service provider name. The abbreviated domain name is therefore displayed next to the source title in README.md. |
| country | String | [Optional] Overwrite default country code which is derived from yaml file name. |
| howto | String | A multi-line string in markdown format which describes the steps to configure the ICS source. |
| test_cases | Dict | A dictionary with test-cases. The key of an entry represents the name of the test-case which will be displayed during testing. The item contains a dictionary of the source arguments. |

Example:

```yaml
title: Entsorgungsgesellschaft Görlitz-Löbau-Zittau
url: https://www.abfall-eglz.de
howto: |
   - Goto <https://www.abfall-eglz.de/abfallkalender.html> and select your municipality.  
   - Right-click on `Entsorgungstermine als iCalendar herunterladen` and copy link address.
   - Replace the `url` in the example configuration with this link.
test_cases:
   Oppach:
       url: "https://www.abfall-eglz.de/abfallkalender.html?ort=Oppach&ortsteil=Ort+Oppach&strasse=&ics=1"
       split_at: " & "
```

## Service Provider Markdown File

The markdown file will be automatically generated from the information in the yaml file. Just call `update_docu_links.py` in the top-level directory. This will also update README.md and info.md automatically.

```bash
./update_docu_links.py
```

## Update Links in README.md and info.md

The `README.md` file in the top level folder contains a list of supported service providers.

The `info.md` is rendered in the HACS user interface within Home Assistant and gives potential users a summary of what the component does, and the service providers supported.

The links in both files can be updated automatically using the script `update_docu_links.py` in the top-level directory:

```bash
./update_docu_links.py
```

## Test the new ICS configuration

Debugging a source script within Home Assistant is not recommended. Home Assistant's start-up process is too slow for fast debugging cycles. To help with debugging/troubleshooting, the Waste Collection Schedule framework contains a command line script that can be used to test source scripts. The script iterates through the `test cases` defined in the source script passing each set of arguments to the source script and prints the results.

The script supports the following options:

| Option | Argument | Description |
|--------|----------|-|
| `-I`   | -        | Test all yaml files. |
| `-y`   | YAML     | yaml file name in folder `/doc/ics/yaml` without ending `.yaml` |
| `-l`   | -        | List all found dates. |
| `-i`   | -        | Add icon name to output. Only effective together with `-l`. |
| `-t`   | -        | Show extended exception info and stack trace. |

For debugging purposes of a single yaml configuration, it is recommended to use the `-y YAML` option. If used without any arguments provided, the script tests every script in the `custom_components/waste_collection_schedule/waste_collection_schedule/source` folder and prints the number of found entries for every test case.

To use it:

1. Navigate to the `/custom_components/waste_collection_schedule/waste_collection_schedule/test/` directory
2. Confirm the `test_sources.py` script is present
3. Execute the test script. For example, testing the abc_com.yaml configuration file would be:

   ```bash
   test_sources.py -y koblenz_de
   ```

4. Confirm the results returned match expectation. For example, testing koblenz_de returns:

   ```text
   Testing ICS koblenz_de
     found 60 entries for Altstadt
   ```

5. To view individual date entries, use the `-l` arguments, for example:

   ```bash
   test_sources.py -y koblenz_de -l
   Testing ICS koblenz_de
     found 60 entries for Altstadt
       2023-04-19 : Altpapier
       2023-05-10 : Altpapier
       2023-06-01 : Altpapier
       2023-06-21 : Altpapier
       2023-07-12 : Altpapier
       ...
   ```
