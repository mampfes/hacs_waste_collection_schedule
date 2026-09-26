# EAD Darmstadt

Support for schedules provided by [EAD Darmstadt](https://ead.darmstadt.de/).

Source script for waste collection in Darmstadt ead.darmstadt.de

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ead_darmstadt_de
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
    - name: ead_darmstadt_de
      args:
        street: "Stresemannstra\xDFe"
```
