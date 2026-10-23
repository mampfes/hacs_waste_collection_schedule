# Gänserndorf City / Gänserndorf App

Support for schedules provided by [Gänserndorf City / Gänserndorf App](https://www.gaenserndorf.at/).

Source for waste collection schedule for the city of Gänserndorf, Austria. Uses the Jolioo mobile app API.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gaenserndorf_city_at
      args:
        street: STREET
        calendar_index: CALENDAR_INDEX
```

### Configuration Variables

**street**  
*(string) (required)*

**calendar_index**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gaenserndorf_city_at
      args:
        street: Baumschulweg
```

## How to get the source arguments

Enter the name of your street as shown in the Gänserndorf App. `calendar_index` (starting at 0) picks the calendar when a street maps to several.
