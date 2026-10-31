# SYVALORM Loir & Sarthe

Support for schedules provided by [SYVALORM Loir & Sarthe](https://www.syvalorm.fr).

Waste collection dates from SYVALORM's published calendars.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: syvalorm_fr
      args:
        municipality: MUNICIPALITY
```

### Configuration Variables

**municipality**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: syvalorm_fr
      args:
        municipality: "Beill\xE9"
```

## How to get the source arguments

Enter your commune as printed on the map in the calendar at https://www.syvalorm.fr/omr-smirgeomes/. Residual waste and packaging are collected together. Only dates in the published annual calendars are returned; current and future calendars are read separately to account for route changes.
