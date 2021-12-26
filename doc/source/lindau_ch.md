# Abfallwirtschaft Zollernalbkreis

Support for schedules provided by [https://www.lindau.ch/abfalldaten](https://www.lindau.ch/abfalldaten).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lindau_ch
      args:
        city: Tagelswangen

```

### Configuration Variables

**city**<br>
*(string) (required)*

Choose one of the following list:
- Grafstal
- Lindau
- Tagelswangen
- Winterberg

or use one the following IDs: 190, 191, 192, 193

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: lindau_ch
      args:
        city: Tagelswangen

```
