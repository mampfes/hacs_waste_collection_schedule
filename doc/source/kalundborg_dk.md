# Kalundborg Kommune

Support for schedules provided by [Kalundborg Kommune](https://kalundborg.dk).

Source for Kalundborg Kommune waste collection schedule

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kalundborg_dk
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
    - name: kalundborg_dk
      args:
        id: 00008d18-0002-0001-4164-647265737320
```

## How to get the source arguments

To get your address ID: go to https://kalundborg.infovision.dk/public/selectaddress and search for your address. You will find the ID in the URL of the address page, e.g. https://kalundborg.infovision.dk/public/address/00006ac8-0002-0001-4164-647265737320, a UUID like `00006ac8-0002-0001-4164-647265737320`.
