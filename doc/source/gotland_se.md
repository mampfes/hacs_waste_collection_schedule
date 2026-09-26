# Region Gotland

Support for schedules provided by [Region Gotland](https://gotland.se).

Source for Region Gotland waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gotland_se
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gotland_se
      args:
        uprn: '0106633415'
```

## How to get the source arguments

Search your address at https://edpfuture.gotland.se/FutureWeb/SimpleWastePickup and use the number in brackets as 'uprn'.
