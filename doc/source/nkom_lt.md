# Nemėžio komunalininkas

Support for schedules provided by [Nemėžio komunalininkas](https://www.nkom.lt/kita.html).

Waste collection schedules for Vilnius District, Lithuania.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nkom_lt
      args:
        location: LOCATION
```

### Configuration Variables

**location**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: nkom_lt
      args:
        location: "Nem\u0117\u017Eis"
```

## How to get the source arguments

Open https://www.nkom.lt/kita.html and use a town, village, or street name as it appears in the 'Vietovė' column of the schedule.
