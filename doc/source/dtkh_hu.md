# DTKH Nonprofit Kft. (Kiskunfélegyháza)

Support for schedules provided by [DTKH Nonprofit Kft. (Kiskunfélegyháza)](https://dtkh.hu).

Source for the Kiskunfélegyháza waste collection calendar of DTKH.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: dtkh_hu
      args:
        weekday: WEEKDAY
        street: STREET
```

### Configuration Variables

**weekday**  
*(string) (required)*

**street**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: dtkh_hu
      args:
        weekday: Monday
```

## How to get the source arguments

Pick the weekday your general waste (vegyes hulladék) is collected; recyclables (szelektív) are collected every other week on the same day (Hétfő = Monday, Kedd = Tuesday, Szerda = Wednesday, Csütörtök = Thursday, Péntek = Friday). Green waste (zöldhulladék) is collected Wednesday to Friday by street: enter your street as printed in the street list (Zöld utcajegyzék) on the back of the yearly calendar at https://dtkh.hu/letoltheto-dokumentumok-kiskunfelegyhaza, e.g. "Petőfi Sándor utca". Where a street is split by house numbers, use the full entry, e.g. "Nádasdy utca 1-5, 2-10"; an ambiguous street lists the possible entries. Leave the street empty to skip green waste.
