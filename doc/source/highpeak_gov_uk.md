# High Peak Borough Council

Support for schedules provided by [High Peak Borough Council](https://www.highpeak.gov.uk/), serving High Peak Borough, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: highpeak_gov_uk
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
    - name: highpeak_gov_uk
      args:
        postcode: SK23 6BQ
        uprn: "10010724045"
        
```

## How to get the source argument

Use your postcode as the `postcode` argument and your Unique Property Reference Number (UPRN) as the `uprn` argument.

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
