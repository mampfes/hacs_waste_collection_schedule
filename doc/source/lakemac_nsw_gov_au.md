# Lake Macquarie City Council

Support for schedules provided by [Lake Macquarie City Council Waste and Recycling](https://www.lakemac.com.au/For-residents/Waste-and-recycling/When-are-your-bins-collected).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lakemac_nsw_gov_au
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
    - name: lakemac_nsw_gov_au
      args:
        address: te
```

## How to get the source arguments

Visit the [Lake Macquarie City Council Waste and Recycling](https://www.lakemac.com.au/For-residents/Waste-and-recycling/When-are-your-bins-collected) page and search for your address.
The argument address should match the first result in the search list.
Only the first match will be collected.