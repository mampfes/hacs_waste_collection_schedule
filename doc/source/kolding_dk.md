# Kolding Kommune

Support for schedules provided by [Kolding Kommune](https://kolding.dk).

Source for Kolding Kommune waste collection schedule

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kolding_dk
      args:
        id: ID
```

### Configuration Variables

**id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kolding_dk
      args:
        id: 00007b76-0002-0001-4164-647265737320
```

## How to get the source arguments

Go to https://kolding.infovision.dk/public/selectaddress and search for your address. Your ID is in the URL, e.g. `00007b8c-0002-0001-4164-647265737320`.
