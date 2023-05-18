# City of Port Adelaide Enfield, South Australia

Support for schedules provided by [City of Port Adelaide Enfield, South Australia](https://ecouncil.portenf.sa.gov.au/), serving City of Port Adelaide Enfield, South Australia, South Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: portenf_sa_gov_au
      args:
        suburb: SUBURB
        street: STREET NAME
        house_number: "HOUSE NUMBER"
        unit_number: UNIT NUMBER
        
```

### Configuration Variables

**suburb**  
*(String) (required)*

**street**  
*(String) (required)*

**house_number**  
*(String | Integer) (required)*

**unit_number**  
*(String | Integer) (optional)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: portenf_sa_gov_au
      args:
        suburb: Rosewater
        street: Addison Road
        house_number: 91
        unit_number: 2
        
```

## How to get the source argument

Find the parameter of your address using [https://www.cityofpae.sa.gov.au/live/waste/bin-collection](https://www.cityofpae.sa.gov.au/live/waste/bin-collection) and write them exactly like the address you get searching for your address.
