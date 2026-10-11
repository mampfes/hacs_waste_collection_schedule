# GVA Baden

Support for schedules provided by [GVA Baden](https://baden.umweltverbaende.at/).

Source for waste collection services Association of Municipalities in the District of Baden

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: baden_umweltverbaende_at
      args:
        region: REGION
        calendar: CALENDAR
```

### Configuration Variables

**region**  
*(string) (required)*

**calendar**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: baden_umweltverbaende_at
      args:
        region: "Soo\xDF"
```

## How to get the source arguments

Enter your municipality (`region`) as it is listed at https://baden.umweltverbaende.at/. A municipality with several collection areas also needs `calendar`, the calendar's name as listed there (for example `ICS Abfuhrbereich 1`). The error message lists the valid values. The `umweltverbaende_at` source serves this district too.
