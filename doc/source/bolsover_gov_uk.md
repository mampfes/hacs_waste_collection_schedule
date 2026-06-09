# Bolsover District Council

Support for schedules provided by [Bolsover District Council](https://www.bolsover.gov.uk), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bolsover_gov_uk
      args:
        calendar: a
        collection_day: wednesday
```

### Configuration Variables

**calendar** *(string) (required)*: Your bin calendar letter. Available values: `a`, `b`.

**collection_day** *(string) (required)*: Your collection day. Available values: `tuesday`, `wednesday`, `thursday`, `friday`.

Find your calendar and collection day at [https://www.bolsover.gov.uk/services/b/bins-and-recycling/](https://www.bolsover.gov.uk/services/b/bins-and-recycling/).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bolsover_gov_uk
      args:
        calendar: "b"
        collection_day: "thursday"
```
