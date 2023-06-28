# Gmags Mönchengladbacher Abfall-, Grün- und Straßenbetriebe AöR

Support for schedules provided by [mags.de](https://mags.de) located in NRW, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mags_de
      args:
        street: Schlossacker
        number: 43
        turnus: 2
```

### Configuration Variables

**street**
*(string) (required)*


**number**
*(number) (required)*


**turnus**
*(number)*

*1* *2* or *4* for n-weekly turnus, 2 by default

## How to get the source arguments

Visit [mags.de](https://mags.de/online-abfuhrkalender) and search for your address in the dropdown menu. The `street` argument should exactly match the result.