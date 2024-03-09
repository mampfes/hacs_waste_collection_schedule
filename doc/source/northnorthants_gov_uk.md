# North Northamptonshire council

Support for schedules provided by [North Northamptonshire council](https://www.northnorthants.gov.uk/), serving North Northamptonshire council, .

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: northnorthants_gov_uk
      args:
        uprn: "UPRN"
        
```

### Configuration Variables

**uprn**  
*(String | Integer) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: northnorthants_gov_uk
      args:
        uprn: "100030987513"
        
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
