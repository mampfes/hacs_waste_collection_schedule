# City of Melville

Support for schedules provided by [City of Melville](https://www.melvillecity.com.au/waste-and-environment/waste-recycling-fogo/residential-bins), Western Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: melvillecity_com_au
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
    - name: melvillecity_com_au
      args:
        address: "43 Williams Road, Melville, WA"
```

## How to get the source arguments

Visit the [City of Melville residential bins](https://www.melvillecity.com.au/waste-and-environment/waste-recycling-fogo/residential-bins) page and search for your address. Use the street address including suburb.
