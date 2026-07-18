# AWV: Abfall Wirtschaftszweckverband Ostthüringen

Support for schedules provided by [AWV: Abfall Wirtschaftszweckverband Ostthüringen](https://www.awv-ot.de/).

Source for AWV: Abfall Wirtschaftszweckverband Ostthüringen.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awv_ot_de
      args:
        city: CITY
        street: STREET
        hnr: HNR
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**hnr**  
*(string) (required)*

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
