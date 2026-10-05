# Moray Council

Support for schedules provided by [Moray Council](https://moray.gov.uk).

Source for Moray Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: moray_gov_uk
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
    - name: moray_gov_uk
      args:
        id: '00013734'
```

## How to get the source arguments

Find your address in the Moray Council bin day finder (https://bindayfinder.moray.gov.uk). The property id is the `id` in the address of your calendar page (`cal_<year>_view.php?id=<id>`); leading zeros may be left out.
