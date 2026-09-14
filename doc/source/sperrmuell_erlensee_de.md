# Abfallkalender Erlensee

Support for schedules provided by [Abfallkalender Erlensee](https://sperrmuell.erlensee.de/), serving Stadt Erlensee, Hessen, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sperrmuell_erlensee_de
      args:
        street: STREET_NAME
```

### Configuration Variables

**street**
*(string) (required)*

The name of the street. Must match exactly one of the options shown in the dropdown on the website.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sperrmuell_erlensee_de
      args:
        street: Am Rathaus
```

## How to find the correct street name

Visit [https://sperrmuell.erlensee.de/?type=reminder](https://sperrmuell.erlensee.de/?type=reminder) and look at the street dropdown to find the exact name for your street.
