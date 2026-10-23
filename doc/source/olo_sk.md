# OLO

Support for schedules provided by [OLO](https://www.olo.sk).

Source for OLO in Bratislava, Slovakia

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: olo_sk
      args:
        street: STREET
        registrationNumber: REGISTRATIONNUMBER
```

### Configuration Variables

**street**  
*(string) (optional)*

**registrationNumber**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: olo_sk
      args:
        registrationNumber: '1353013'
```
