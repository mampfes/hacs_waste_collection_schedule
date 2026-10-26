# C.B.B.O.

Support for schedules provided by [C.B.B.O.](https://www.cbbo.it).

Source for C.B.B.O. (Brescia province) door-to-door collection calendars: Capriano del Colle, Ghedi, Montichiari and more.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cbbo_it
      args:
        comune: COMUNE
```

### Configuration Variables

**comune**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cbbo_it
      args:
        comune: Capriano del Colle
```

## How to get the source arguments

Enter your comune as listed on https://www.cbbo.it/ (menu 'Comuni'), e.g. `Capriano del Colle`. The dates are read from the comune's yearly Ecocalendario PDF. Barbariga and San Zeno Naviglio publish a calendar in another layout and are not supported yet.
