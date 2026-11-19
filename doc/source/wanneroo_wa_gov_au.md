# City of Wanneroo

Support for schedules provided by [City of Wanneroo](https://www.wanneroo.wa.gov.au/), serving City of Wanneroo, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: wanneroo_wa_gov_au
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
    - name: wanneroo_wa_gov_au
      args:
        address: 1 Atlanta DR TWO ROCKS
        
```

## How to get the source argument

Find the parameter of your address using [https://www.wanneroo.wa.gov.au/residential-services/waste-and-recycling/bin-collections](https://www.wanneroo.wa.gov.au/residential-services/waste-and-recycling/bin-collections) and write them exactly like on the web page.
