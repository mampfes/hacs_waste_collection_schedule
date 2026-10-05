# Stavanger Kommune

Support for schedules provided by [Stavanger Kommune](https://www.stavanger.kommune.no/).

Source for Stavanger Kommune, Norway

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stavanger_no
      args:
        id: ID
        municipality: MUNICIPALITY
        gnumber: GNUMBER
        bnumber: BNUMBER
        snumber: SNUMBER
```

### Configuration Variables

**id**  
*(string) (required)*

**municipality**  
*(string) (required)*

**gnumber**  
*(string) (required)*

**bnumber**  
*(string) (required)*

**snumber**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stavanger_no
      args:
        id: 57bf9d36-722e-400b-ae93-d80f8e354724
        municipality: Stavanger
        gnumber: '57'
        bnumber: '922'
        snumber: '0'
```
