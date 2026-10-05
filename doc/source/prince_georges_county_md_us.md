# Prince George's County, MD

Support for schedules provided by [Prince George's County, MD](https://www.princegeorgescountymd.gov/departments-offices/environment/waste-recycling/residential-collections).

Source for Prince George's County, Maryland curbside trash, recycling, bulky trash, and yard trim collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: prince_georges_county_md_us
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
    - name: prince_georges_county_md_us
      args:
        address: 6807 McCormick Rd, Upper Marlboro, MD
```

## How to get the source arguments

Enter the full street address including city and state.
