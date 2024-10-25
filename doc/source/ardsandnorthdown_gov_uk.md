# Ards and North Down Borough Council

Support for schedules provided by [Ards and North Down Borough Council](https://ardsandnorthdown.gov.uk), serving Ards and North Down Borough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: ardsandnorthdown_gov_uk
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
    - name: ardsandnorthdown_gov_uk
      args:
        uprn: "185833845"
        
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
