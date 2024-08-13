# West Oxfordshire District Council

Support for schedules provided by [West Oxfordshire District Council](https://westoxon.gov.uk/), serving West Oxfordshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: westoxon_gov_uk
      args:
        address: ADDRESS
        
```

### Configuration Variables

**address**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: westoxon_gov_uk
      args:
        address: 75 manor road woodstock, ox20 1xr
        
```

## How to get the source argument

Visit <https://www.westoxon.gov.uk/bins-and-recycling/check-your-collection-day/> and search for your address, write it exactly as autocompleted by the input form.
