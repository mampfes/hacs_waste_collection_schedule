# City of San Antonio

Support for schedules provided by [City of San Antonio](https://www.sa.gov/Directory/Departments/SWMD/Garbage/My-Collection-Day).

Source for City of San Antonio, Texas waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sanantonio_gov
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
    - name: sanantonio_gov
      args:
        address: 646 S Flores St
```

## How to get the source arguments

The source argument is the street number and street name to the house with waste collection. The address can be tested [here](https://www.sa.gov/Directory/Departments/SWMD/Brush-Bulky/My-Collection-Day).
