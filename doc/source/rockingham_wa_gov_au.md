# City of Rockingham

Support for schedules provided by [City of Rockingham](https://rockingham.wa.gov.au/your-services/waste-and-recycling/bin-collection).

Source for the City of Rockingham rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rockingham_wa_gov_au
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
    - name: rockingham_wa_gov_au
      args:
        suburb: Baldivis
        street_name: Makybe Drive
        street_number: '59'
```
