# Stadt Gemünden (Wohra)

Support for schedules provided by [Stadt Gemünden (Wohra)](https://www.gemuenden-wohra.de).

Source for Stadt Gemünden (Wohra) waste collection schedule.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gemuenden_wohra_de
      args:
        tour: TOUR
```

### Configuration Variables

**tour**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gemuenden_wohra_de
      args:
        tour: 1
```

## How to get the source arguments

Tour 1: Schiffelbach, Ellnrode, Grüsen, Sehlen, Herbelhausen, Lehnhausen and areas west of the former railway line. Tour 2: rest of the Gemünden town centre.
