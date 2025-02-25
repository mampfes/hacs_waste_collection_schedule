# Rochdale Borough Council

Support for schedules provided by [Rochdale Borough Council](https://www.rochdale.gov.uk/), serving Rochdale, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: rochdale_gov_uk
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
    - name: rochdale_gov_uk
      args:
        postcode: OL104TJ
        uprn: "10094359340"
```

## How to get the source argument

Use your postcode as the `postcode` argument and your Unique Property Reference Number (UPRN) as the `uprn` argument.

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
