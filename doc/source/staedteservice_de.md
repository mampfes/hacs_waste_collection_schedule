# Staedteservice Raunheim Rüsselsheim

Support for schedules provided by [staedteservice.de](https://www.staedteservice.de/leistungen/abfallwirtschaft/abfallkalender/index.html) location Raunheim and Rüsselsheim.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: staedteservice_de
      args:
        city: CITY
        street_number: STREET NUMBER
```

### Configuration Variables

**city**  
*(string) (required)*

**street_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: staedteservice_de
      args:
        city: "Raunheim"
        street_number: "565"
```

## How to get the source arguments

1. Visit [https://www.staedteservice.de/leistungen/abfallwirtschaft/abfallkalender/index.html](https://www.staedteservice.de/leistungen/abfallwirtschaft/abfallkalender/index.html).
2. Select your `city` + `street` and hit Next (Weiter).
3. Search for the Link to the ical file. Copy the link or just hover it. It should have the following format: `https://www.staedteservice.de/abfallkalender_2_550_2022.ics`.
4. Your `street_number` is the number before the year (number in the center). In the example above the `street_number` is the `550`.
