# City of Kalamunda

Support for schedules provided by [City of Kalamunda](https://www.kalamunda.wa.gov.au/kerbside-3-bin-system/collection-days/bin-day).

Source for the City of Kalamunda rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kalamunda_wa_gov_au
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
    - name: kalamunda_wa_gov_au
      args:
        suburb: Kalamunda
        street_name: Railway Road
        street_number: '43'
```
