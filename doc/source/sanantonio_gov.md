# City of San Antonio

Support for schedules provided by [City of San Antonio](https://www.sa.gov/Directory/Departments/SWMD/Brush-Bulky/My-Collection-Day), Texas, USA

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
*(String) (required)*

Number and name of the street address.


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: sanantonio_gov
      args:
        address: 646 S Flores St
        
```

## How to get the source argument

The source argument is the street number and street name to the house with waste collection.
The address can be tested [here](https://www.sa.gov/Directory/Departments/SWMD/Brush-Bulky/My-Collection-Day).
