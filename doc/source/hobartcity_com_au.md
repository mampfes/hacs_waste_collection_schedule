# City of Hobart

Support for schedules provided by [City of Hobart](https://www.hobartcity.com.au).

Source for City of Hobart

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hobartcity_com_au
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
    - name: hobartcity_com_au
      args:
        address: 154 FOREST ROAD, WEST HOBART 7000
```

## How to get the source arguments

The address should exactly match the address autocompleted by the website: https://www.hobartcity.com.au/Residents/Waste-and-recycling/When-is-my-bin-collected
