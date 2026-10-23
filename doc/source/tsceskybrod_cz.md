# Technické služby Český Brod

Support for schedules provided by [Technické služby Český Brod](https://www.tsceskybrod.cz/).

Source for waste collection in Český Brod

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tsceskybrod_cz
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
    - name: tsceskybrod_cz
      args:
        street: "n\xE1m. Arno\u0161ta z Pardubic"
```

## How to get the source arguments

Visit https://www.tsceskybrod.cz/pravidelny-svoz-odpadu and enter the street or location name exactly as listed in the table.
