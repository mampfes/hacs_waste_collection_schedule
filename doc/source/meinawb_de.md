# Abfallwirtschaftsbetrieb Landkreis Ahrweiler (AWB)

Support for schedules provided by [Abfallwirtschaftsbetrieb Landkreis Ahrweiler](https://www.meinawb.de/) located in Rhineland Palatinate, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: meinawb_de
      args:
        city: CITY
        street: STREET
        house_number: HNR
        address_suffix: HNR_SUFFIX
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(integer) (required)*

**address_suffix**  
*(string) (optional) (default: "")*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: meinawb_de
      args:
        city: Oberzissen
        street: Ackerstrasse
        address_suffix: 1
```

## How to get the source arguments

The arguments are your address. The input validation is a bit petty, so make sure you write it exactly like in the [web form](https://www.meinawb.de/abfuhrtermine). For troubleshooting, have a look in the home assistant logs.
