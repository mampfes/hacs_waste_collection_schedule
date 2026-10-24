# McNamara Waste Services

Support for schedules provided by [McNamara Waste Services](https://www.mcwaste.com).

Source for McNamara Waste Services (Massachusetts) trash and recycling collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mcwaste_com
      args:
        collection_day: COLLECTION_DAY
        recycling_week: RECYCLING_WEEK
```

### Configuration Variables

**collection_day**  
*(string) (required)*

**recycling_week**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mcwaste_com
      args:
        collection_day: Tuesday
        recycling_week: A
```

## How to get the source arguments

Choose your trash day and your recycling week (A or B). The town lists linked from https://www.mcwaste.com/ (Hampden, Wilbraham) give both for every street; elsewhere ask McNamara (413-566-8322).
