# Shellharbour City Council

Support for schedules provided by [Shellharbour City Council](https://shellharbourwaste.com.au).

Source script for shellharbourwaste.com.au

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: shellharbourwaste_com_au
      args:
        zoneID: ZONEID
```

### Configuration Variables

**zoneID**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: shellharbourwaste_com_au
      args:
        zoneID: Monday A
```

## How to get the source arguments

Enter your collection zone as shown on https://www.shellharbourwaste.com.au/find-my-bin-day/ (e.g. 'Monday A').
