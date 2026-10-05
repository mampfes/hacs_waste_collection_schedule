# Round Rock Texas

Support for schedules provided by [Round Rock Texas](https://www.roundrocktexas.gov/).

Source for bin collection services for Round Rock, Texas

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: roundrocktexas_gov
      args:
        neighborhood: NEIGHBORHOOD
```

### Configuration Variables

**neighborhood**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: roundrocktexas_gov
      args:
        neighborhood: Apache Oaks
```

## How to get the source arguments

Enter the name of your neighborhood as the City of Round Rock lists it (for example Apache Oaks or Windy Park). Recycling is collected every two weeks and trash weekly, on the weekday of your neighborhood's recycling zone.
