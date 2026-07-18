# Abfallbehandlungsgesellschaft Havelland mbH (abh)

Support for schedules provided by [Abfallbehandlungsgesellschaft Havelland mbH (abh)](https://abfall-havelland.de/).

Source for Abfallbehandlungsgesellschaft Havelland mbH.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_havelland_de
      args:
        ort: ORT
        strasse: STRASSE
```

### Configuration Variables

**ort**  
*(string) (required)*

**strasse**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_havelland_de
      args:
        ort: Wustermark
        strasse: Drosselgasse
```
