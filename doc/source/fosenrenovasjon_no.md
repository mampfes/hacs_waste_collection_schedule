# Fosen Renovasjon

Support for schedules provided by [Fosen Renovasjon](https://fosenrenovasjon.no/).

Source for Fosen Renovasjon.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: fosenrenovasjon_no
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: fosenrenovasjon_no
      args:
        address: Lysøysundveien 117
```
