# AWG Wuppertal

Support for schedules provided by [AWG Wuppertal](https://awg-wuppertal.de).

Source for AWG Wuppertal.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awg_wuppertal_de
      args:
        street: STREET
```

### Configuration Variables

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awg_wuppertal_de
      args:
        street: "Hauptstra\xDFe"
```
