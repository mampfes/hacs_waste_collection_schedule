# WSZ-Moosburg.at

Support for schedules provided by [wsz-moosburg.at](https://wsz-moosburg.at).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wsz-moosburg_at
      args:
        address_id: ID
```

### Configuration Variables

**address_id**<br>
*(integer) (required)*

## How to get the source arguments

### Simple Variant: Use wizard script

There is a script with an interactive command line interface which generates the required source configuration:

[https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/wsz-moosburg_at.py](https://github.com/mampfes/hacs_waste_collection_schedule/blob/master/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/wsz-moosburg_at.py).

First, install the Python module `inquirer`. Then run this script from a shell and answer the questions.

### Slightly Harder Variant: Extract argument from website

Another way get the source arguments is to us a (desktop) browser with developer tools, e.g. Google Chrome:

1. Open [https://wsz-moosburg.at/calendar](https://wsz-moosburg.at/calendar).
2. Open the Developer Tools (Ctrl + Shift + I / Cmd + Option + I) and open the `Network` tab.
3. Select your `Gemeinde` from the list.
4. Select your `Addresse` from the list.
5. There might be another step to select your `Straße`, but this depends on the address. If it's prompted to you, select that as well.
6. Select the last entry in the `Network` tab's list, it should be a number followed by `?include-public-holidays`, e.g. `69980?include-public-holidays`.
7. This number (e.g. `69980`) is what needs to be used as `address_id` in the configuration.