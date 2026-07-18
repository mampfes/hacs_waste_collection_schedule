# Fredrikstad kommune

Support for schedules provided by [Fredrikstad kommune](https://www.fredrikstad.kommune.no).

Source for Fredrikstad kommune waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: fredrikstad_no
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
    - name: fredrikstad_no
      args:
        address: Kanelveien 4
```
