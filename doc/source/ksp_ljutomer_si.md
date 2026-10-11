# KSP Ljutomer

Support for schedules provided by [KSP Ljutomer](https://ksp-ljutomer.si).

Source for KSP Ljutomer (Apače, Križevci, Ljutomer, Razkrižje, Veržej), Slovenia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ksp_ljutomer_si
      args:
        calendar: CALENDAR
```

### Configuration Variables

**calendar**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ksp_ljutomer_si
      args:
        calendar: Ljutomer (torek)
```

## How to get the source arguments

Choose your municipality. In Ljutomer the calendar depends on the collection weekday; each calendar on https://ksp-ljutomer.si/dejavnosti/ravnanje-z-odpadki/koledarji-zbiranja-komunalnih-odpadkov/ lists the settlements and streets it covers.
