# Wakefield UK

Support for schedules provided by [Wakefield UK](https://www.wakefield.gov.uk), serving Wakefield UK, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: wakefield_gov_uk
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
    - name: wakefield_gov_uk
      args:
        uprn: "63077775"
        
```

## How to get the source argument

Find the parameter of your address using [https://www.wakefield.gov.uk/where-i-live/](https://www.wakefield.gov.uk/where-i-live/) and write them exactly like on the web page.
