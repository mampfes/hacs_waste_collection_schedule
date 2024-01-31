# Barnsley Metropolitan Borough Council

Support for schedules provided by [Barnsley Metropolitan Borough Council](https://barnsley.gov.uk), serving Barnsley Metropolitan Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: barnsley_gov_uk
      args:
        postcode: POSTCODE
        uprn: "UPRN"
        
```

### Configuration Variables

**postcode**  
*(String) (required)*

**uprn**  
*(String | Integer) (required)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: barnsley_gov_uk
      args:
        postcode: S71 1EE
        uprn: "100050671689"
        
```

## How to get the source argument

Use your postcode as the `postcode` argument and your Unique Property Reference Number (UPRN) as the `uprn` argument.

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
