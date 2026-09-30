# TBV Velbert

Support for schedules provided by [TBV Velbert](https://www.tbv-velbert.de).

Source script for tbv-velbert.de, germany

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tbv_velbert_de
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
    - name: tbv_velbert_de
      args:
        street: Am Lindenkamp 33
```

## How to get the source arguments

Straße und Hausnummer so eingeben, wie sie im Abfallkalender auf tbv-velbert.de/abfall gesucht werden, z. B. 'Am Lindenkamp 33'.
