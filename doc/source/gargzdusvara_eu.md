# Gargždų švara

Support for schedules provided by [VšĮ "Gargždų švara"](https://www.gargzdusvara.eu), the waste collection company for Klaipėda district municipality (Lithuania).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gargzdusvara_eu
      args:
        location: LOCATION
```

### Configuration Variables

**location**  
*(string) (required)*

The exact location/street-group name as shown in the "Pasirinkite vietovę" (select location) dropdown on the [schedules page](https://www.gargzdusvara.eu/atlieku-isvezimo-grafikai/) after picking any waste type first. Must match exactly, including Lithuanian diacritics.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gargzdusvara_eu
      args:
        location: Klemiškės I k.
```

## How to get the source argument

Visit the [Atliekų išvežimo grafikai](https://www.gargzdusvara.eu/atlieku-isvezimo-grafikai/) page, select any waste type ("Pasirinkite atliekų tipą") to populate the location dropdown, then find your street/settlement group in "Pasirinkite vietovę". Use that exact text as the `location` argument.
