# City of Onkaparinga Council

Support for schedules provided by [City of Onkaparinga Council Waste and Recycling](https://www.onkaparingacity.com/Services/Waste-and-recycling/Bin-collections).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: onkaparingacity_com
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
    - name: onkaparingacity_com
      args:
        address: 18 Flagstaff Road, FLAGSTAFF HILL 5159
```

## How to get the source arguments

Visit the [City of Onkaparinga Council Waste and Recycling](https://www.onkaparingacity.com/Services/Waste-and-recycling/Bin-collections) page and search for your address.
The argument address should match the first result in the search list.
Only the first match will be collected.
