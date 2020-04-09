# Abfall Kreis Tuebingen

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_kreis_tuebingen
      args:
        ort: ORT
        dropzone: DROPZONE
        ics_with_drop: ICS_WITH_DROP
```

### Configuration Variables

**ort**<br>
*(integer) (required)*

**dropzone**<br>
*(integer) (required)*

**ics_with_drop**<br>
*(boolean) (optional, default: ```False```)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_kreis_tuebingen
      args:
        ort: 3
        dropzone: 525
```