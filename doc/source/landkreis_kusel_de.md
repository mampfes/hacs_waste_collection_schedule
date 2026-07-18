# Landkreis Kusel

Support for schedules provided by [Landkreis Kusel](https://www.landkreis-kusel.de/).

Source for Landkreis Kusel.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_kusel_de
      args:
        ortsgemeinde: ORTSGEMEINDE
```

### Configuration Variables

**ortsgemeinde**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_kusel_de
      args:
        ortsgemeinde: Adenbach
```
