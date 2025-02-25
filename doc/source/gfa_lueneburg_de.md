# GFA Lüneburg

Support for schedules provided by [GFA Lüneburg](https://www.gfa-lueneburg.de/service/abfuhrkalender.html), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gfa_lueneburg_de
      args:
        city: CITY
        street: STREET
        house_number: HNR
```

### Configuration Variables

**city**  
_(string) (required)_

**street**  
_(string) (required)_

**house_number**  
_(integer) (required)_

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gfa_lueneburg_de
      args:
        city: "Dahlem"
        street: "Hauptstr"
        house_number: 7
```

```yaml
waste_collection_schedule:
  sources:
    - name: gfa_lueneburg_de
      args:
        city: Wendish Evern
        street: Kückenbrook
        house_number: 5 A
```

## How to get the source arguments

These values are the location you want to query for. Make sure, the writing is exactly as it is on <https://www.gfa-lueneburg.de/service/abfuhrkalender.html>. Typos will result in an parsing error which is printed in the log.
