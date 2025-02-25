# City of Hobart

Support for schedules provided by the [City of Hobart](https://www.hobartcity.com.au), Australia.

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
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: hobartcity_com_au
      args:
        address: 154  FOREST ROAD, WEST HOBART Tasmania 7000
```

## How to get the source argument

Find the parameter of your address using <https://www.hobartcity.com.au/Residents/Waste-and-recycling/When-is-my-bin-collected> and write them exactly like on the web page.
