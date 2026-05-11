# Gänserndorf City / Gänserndorf App

Support for schedules provided by [Gänserndorf City](https://www.gaenserndorf.at/) located in Gänserndorf, Austria. Uses the Jolioo mobile app API.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gaenserndorf_city_at
      args:
        street: STREET
```

### Configuration Variables

**street**  
*(string) (required)*

The name of your street, e.g. `"Baumschulweg"`.

**calendar_index**  
*(integer) (optional, default: `0`)*

Some streets map to multiple waste calendars. Use this to select which calendar to use (starting at `0`).

### How to get the source arguments

Use the street name as shown in the [Gänserndorf App](https://www.gans-gaenserndorf.at/).
If you have misspelled your street, check the debug output for all the valid streetnames which will be returned there.

If your street has multiple calendars, you can specify the `calendar_index` parameter.

### Waste types

Please check the app for the waste types in your area as these names are the waste types it will return.
Some of the most common waste types are:

* Biomüll
* Sondermüll
* Restmüll
* Restmüll Wohnblöcke 2-Wochen-Tour
* Altpapier Großcontainer
* Leicht- & Metallverpackungen/Gelbe Tonne/Gelber Sack

## Examples

**Simple**

```yaml
waste_collection_schedule:
  sources:
    - name: gaenserndorf_city_at
      args:
        street: "Baumschulweg"
```

**Street with multiple calendars**

```yaml
waste_collection_schedule:
  sources:
    - name: gaenserndorf_city_at
      args:
        street: "Siebenbrunner Straße"
        calendar_index: 0
```
