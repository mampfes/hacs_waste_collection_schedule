# ZAB Bazenheid, Switzerland

Support for schedules provided by [Zweckverband Abfallverwertung Bazenheid (ZAB)](https://zab.citymobile.ch), covering municipalities in the Toggenburg, Wil and Untertoggenburg regions of north-eastern Switzerland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: zab_ch
      args:
        municipality: MUNICIPALITY
        district: DISTRICT  # optional, only required for municipalities split into sub-districts
```

### Configuration Variables

**municipality**
*(string) (required)*

**district**
*(string) (optional)*

Only required for municipalities whose waste schedules are split into multiple sub-districts. If you don't supply one for such a municipality, the integration will raise an error listing the valid options to choose from.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: zab_ch
      args:
        municipality: Wängi
```

```yaml
waste_collection_schedule:
  sources:
    - name: zab_ch
      args:
        municipality: Eschlikon
        district: Kehrichtsammlung Eschlikon
```

## How to get the source arguments

Open the [ZAB Gemeinden listing](https://zab.citymobile.ch/index.php?apid=2326631&apparentid=16145265) and pick your municipality. If the next page shows multiple sub-collection areas, the title shown next to each is the value to supply as `district`.
