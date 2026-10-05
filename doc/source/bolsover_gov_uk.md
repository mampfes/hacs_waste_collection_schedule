# Bolsover District Council

Support for schedules provided by [Bolsover District Council](https://www.bolsover.gov.uk).

Source for Bolsover District Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bolsover_gov_uk
      args:
        calendar: CALENDAR
        collection_day: COLLECTION_DAY
```

### Configuration Variables

**calendar**  
*(string) (required)*

**collection_day**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bolsover_gov_uk
      args:
        calendar: a
        collection_day: wednesday
```

## How to get the source arguments

Check your bin calendar letter (A or B) and collection day (Tuesday to Friday) on the Bolsover website at https://www.bolsover.gov.uk/services/b/bins-and-recycling/.
