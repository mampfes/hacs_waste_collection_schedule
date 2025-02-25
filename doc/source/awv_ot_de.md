# AWV: Abfall Wirtschaftszweckverband Ostthüringen

Support for schedules provided by [AWV: Abfall Wirtschaftszweckverband Ostthüringen](https://www.awv-ot.de/), serving Ostthüringen, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: awv_ot_de
      args:
        city: CITY (Ort)
        street: STREET (Straße)
        hnr: HNR (Housenummer)
        
```

### Configuration Variables

**city**  
*(String) (required)*

**street**  
*(String) (required)*

**hnr**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: awv_ot_de
      args:
        city: Bethenhausen OT Caasen
        street: Caasen
        hnr: 15A
```

## How to get the source argument

Find the parameter of your address using [https://www.awv-ot.de/www/awvot/abfuhrtermine/leerungstage/](https://www.awv-ot.de/www/awvot/abfuhrtermine/leerungstage/) and write them exactly like on the web page.
