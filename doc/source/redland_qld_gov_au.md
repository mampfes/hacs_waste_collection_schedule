# Redland City Council (QLD)

Support for schedules provided by [Redland City Council (QLD)](https://www.redland.qld.gov.au).

Source for Redland City Council (QLD) rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: redland_qld_gov_au
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
    - name: redland_qld_gov_au
      args:
        suburb: Mount Cotton
        street_name: Mount Cotton Road
        street_number: '1261'
```
