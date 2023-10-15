# City of Greater Geelong

Support for schedules provided by [City of Greater Geelong](https://www.geelongaustralia.com.au/recycling/calendar.aspx).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: geelongaustralia_com_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: geelongaustralia_com_au
      args:
        address: 155 Mercer Street Geelong 3220
```

## How to get the source arguments

The address needs to be an exact match for what the City of Greater Geelong website expects. You can attempt to search your address on the [website](https://www.geelongaustralia.com.au/recycling/calendar.aspx) to find the expected format for your address.
