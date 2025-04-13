# North Warwickshire Borough Council

Support for schedules provided by [North Warwickshire Borough Council](https://www.northwarks.gov.uk/bincalendar), serving North Warwickshire District, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: northwarks_gov_uk
      args:
        house_number: "HOUSE_NUMBER"
        street: "STREET"
        postcode: "POSTCODE"
        
```

### Configuration Variables

**house_number**  
*(String | Integer) (required)*


**street**  
*(String) (required)*


**postcode**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: northwarks_gov_uk
      args:
        house_number: 43
        street: "Laburnum Close"
        postcode: "B78 2JH"
        
```


