# Denbighshire County Council

Support for schedules provided by [Denbighshire County Council](https://www.denbighshire.gov.uk/), serving Denbighshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: denbighshire_gov_uk
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
    - name: denbighshire_gov_uk
      args:
        uprn: "200003177805"
        
```

## How to get the source argument

To discover your Unique Property Reference Number (UPRN), go to <https://www.findmyaddress.co.uk/> and enter your address details.
