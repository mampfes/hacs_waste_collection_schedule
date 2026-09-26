# New York City

Support for schedules provided by [New York City](https://www.nyc.gov).

Source for New York City, US.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nyc_gov
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
    - name: nyc_gov
      args:
        address: 120-55 Queens Blvd, Kew Gardens, NY 11424
```
