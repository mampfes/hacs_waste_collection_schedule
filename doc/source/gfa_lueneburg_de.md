# Abfallwirtschaftsbetrieb Emsland

Support for schedules provided by [Emsland Abfallwirtschaftsbetrieb](https://www.awb-emsland.de/), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awb_emsland_de
      args:
        city: CITY
        street: STREET
        house_number: HNR
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(integer) (required)*


## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awb_emsland_de
      args:
        city: "Dahlem"
        street: "Hauptstr"
        house_number: 7
```

```yaml
waste_collection_schedule:
  sources:
    - name: awb_emsland_de
      args:
        city: Wendish Evern
        street: Kückenbrook
        house_number: 5 A
```

## How to get the source arguments

These values are the location you want to query for. Make sure, the writing is exactly as it is on <https://www.gfa-lueneburg.de/service/abfuhrkalender.html>. Typos will result in an parsing error which is printed in the log.
