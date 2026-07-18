# Winterthur

Support for schedules provided by [Winterthur](https://winterthur.ch/).

Source for Winterthur.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: winterthur_ch
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
    - name: winterthur_ch
      args:
        street: Am Iberghang
```
