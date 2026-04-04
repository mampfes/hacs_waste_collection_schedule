# City of Kalamunda

Support for schedules provided by [City of Kalamunda](https://www.kalamunda.wa.gov.au/kerbside-3-bin-system/collection-days).

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
        suburb: High Wycombe
        street_name: Wem Mews
        street_number: 27
```

## How to get the source arguments
