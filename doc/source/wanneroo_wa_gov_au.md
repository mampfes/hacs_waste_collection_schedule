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

Search for your address in the "Find your bin collection day" box at [https://www.wanneroo.wa.gov.au/residential-services/waste-and-recycling/bin-collections](https://www.wanneroo.wa.gov.au/residential-services/waste-and-recycling/bin-collections) and use the address exactly as it is suggested there, e.g. `23 Bakana LP LANDSDALE`. Spelled-out street types (`23 Bakana Loop, Landsdale`) are also accepted.

For a unit, include the unit number as shown on the website, e.g. `13/26 Princeton CIR ALEXANDER HEIGHTS`.
