# Dillingen Saar

Support for schedules provided by [Dillingen Saar](https://www.dillingen-saar.de/).

Source script for waste collection Dillingen Saar

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: dillingen_saar_de
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
    - name: dillingen_saar_de
      args:
        street: Am Fischerberg
```
