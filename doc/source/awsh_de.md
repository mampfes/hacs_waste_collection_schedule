# AWSH

Support for schedules provided by [AWSH](https://www.awsh.de)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awsh_de
      args:
        city: CITY
        street: STREET
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: awsh_de
      args:
        city: Reinbek
        street: Ahornweg
```
