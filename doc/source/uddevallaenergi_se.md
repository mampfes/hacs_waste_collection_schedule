# Uddevalla Energi

Support for schedules provided by [Uddevalla Energi](https://www.uddevallaenergi.se/privat/sophamtning.html).

Source for Uddevalla Energi waste collection schedules.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: uddevallaenergi_se
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
    - name: uddevallaenergi_se
      args:
        address: "Fj\xE4llv\xE4gen 11, Ljungskile"
```

## How to get the source arguments

Search for your address on the Uddevalla Energi waste collection webpage and enter it exactly as shown, including the town, e.g. `Fjällvägen 11, Ljungskile`.
