# Ealing Council

Support for schedules provided by [Ealing Council](https://www.ealing.gov.uk), serving Ealing, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: ealing_gov_uk
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
    - name: ealing_gov_uk
      args:
        uprn: "12081500"
        
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
