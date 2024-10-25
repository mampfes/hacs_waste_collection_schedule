# Hull City Council

Support for schedules provided by [Hull City Council](https://hull.gov.uk/), serving Hull, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: hull_gov_uk
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
    - name: hull_gov_uk
      args:
        uprn: "21095794"
        
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
