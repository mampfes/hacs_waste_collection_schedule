# Movar IKS

Support for schedules provided by [Movar IKS](https://movar.no).

Source script for movar.no

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: movar_no
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
    - name: movar_no
      args:
        address: "V\xE5lerveien 1148, V\xE5ler"
```
