# AJL - Abfallwirtschaftsgesellschaft Jerichower Land mbH

Support for schedules provided by [AJL - Abfallwirtschaftsgesellschaft Jerichower Land mbH](https://www.ajl-mbh.de).

Source for AJL - Abfallwirtschaftsgesellschaft Jerichower Land mbH, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ajl_mbh_de
      args:
        town: TOWN
        street: STREET
```

### Configuration Variables

**town**  
*(string) (required)*

**street**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ajl_mbh_de
      args:
        town: Biederitz
```
