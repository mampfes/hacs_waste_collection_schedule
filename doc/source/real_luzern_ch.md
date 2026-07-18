# Real Luzern

Support for schedules provided by [Real Luzern](https://www.real-luzern.ch).

Source script for Real Luzern, Switzerland

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: real_luzern_ch
      args:
        municipality_id: MUNICIPALITY_ID
        street_id: STREET_ID
```

### Configuration Variables

**municipality_id**  
*(string) (required)*

**street_id**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: real_luzern_ch
      args:
        municipality_id: 13
        street_id: 766
```
