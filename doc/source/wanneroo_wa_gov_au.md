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
        address: 23 Bakana Loop LANDSDALE
        
```

## How to get the source argument

Find the parameter of your address using [https://www.wanneroo.wa.gov.au/info/20008/waste_services](https://www.wanneroo.wa.gov.au/info/20008/waste_services) and write them exactly like on the web page.
