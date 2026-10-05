# Erlensee

Support for schedules provided by [Erlensee](https://sperrmuell.erlensee.de/).

Source for waste collection in Erlensee, Hessen.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sperrmuell_erlensee_de
      args:
        street: STREET
```

### Configuration Variables

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sperrmuell_erlensee_de
      args:
        street: Am Rathaus
```

## How to get the source arguments

Go to https://sperrmuell.erlensee.de/ and look up the exact street name in the dropdown.
