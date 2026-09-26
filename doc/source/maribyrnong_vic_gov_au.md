# Maribyrnong Council

Support for schedules provided by [Maribyrnong Council](https://www.maribyrnong.vic.gov.au/Residents/Bins-and-recycling).

Source for Maribyrnong Council (VIC) rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: maribyrnong_vic_gov_au
      args:
        suburb: SUBURB
        street_name: STREET_NAME
        street_number: STREET_NUMBER
```

### Configuration Variables

**suburb**  
*(string) (required)*

**street_name**  
*(string) (required)*

**street_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: maribyrnong_vic_gov_au
      args:
        suburb: Footscray
        street_name: Ballarat Rd
        street_number: 70-100
```
