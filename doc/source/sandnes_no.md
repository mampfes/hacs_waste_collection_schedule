# Sandnes Kommune

Support for schedules provided by [Sandnes Kommune](https://www.sandnes.kommune.no/).

Source for Sandnes Kommune, Norway

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sandnes_no
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
    - name: sandnes_no
      args:
        id: 181e5aac-3c88-4b0b-ad46-3bd246c2be2c
        municipality: Sandnes kommune 2020
        gnumber: '62'
        bnumber: '281'
        snumber: '0'
```
