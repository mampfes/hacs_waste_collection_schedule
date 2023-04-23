# Rotherham Metropolitan Borough Council

Support for schedules provided by [Rotherham Metropolitan Borough Council](https://www.rotherham.gov.uk), serving Rotherham Metropolitan Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: rotherham_gov_uk
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
    - name: rotherham_gov_uk
      args:
        uprn: "100050846673"
        
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.
Otherwise you can search your address on (rotherham.gov.uk)[https://www.rotherham.gov.uk/homepage/333/bin-collection-dates]. When you see your next collections, the uprn can be found in the url as `address`.
