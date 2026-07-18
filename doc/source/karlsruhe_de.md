# City of Karlsruhe

Support for schedules provided by [City of Karlsruhe](https://www.karlsruhe.de/).

Source for City of Karlsruhe.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: karlsruhe_de
      args:
        street: STREET
        hnr: HNR
        ladeort: LADEORT
```

### Configuration Variables

**street**  
*(string) (required)*

**hnr**  
*(string) (required)*

**ladeort**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: karlsruhe_de
      args:
        street: "\xD6stliche Rheinbr\xFCckenstra\xDFe"
        hnr: 1
```
