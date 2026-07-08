# Müllmann-App

Support for waste collection schedules provided by [Müllmann-App](https://muellmann-app.de/), covering several municipalities around Lake Constance (Bodensee), Germany, plus Karlsruhe.

## Supported Municipalities

- Aach
- Allensbach
- Bodman-Ludwigshafen
- Gailingen am Hochrhein
- Hohenfels
- Karlsruhe (street name required)
- Konstanz (street name required)
- Moos
- Mühlhausen-Ehingen
- Mühlingen
- Orsingen-Nenzingen
- Radolfzell am Bodensee (street name required)
- Reichenau
- Singen (Hohentwiel) (street name required)
- Stockach (street name required)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: muellmann_app_de
      args:
        city: Radolfzell
        street: Mooser Straße
```

### Configuration Variables

**city**
*(string) (required)*

Name of the municipality, e.g. `Radolfzell` or `Konstanz`. Use the spelling from the list above (small deviations, like missing umlauts, are tolerated).

**street**
*(string) (optional)*

Street name. Only required for the municipalities marked "street name required" above (Karlsruhe, Konstanz, Radolfzell, Singen (Hohentwiel), Stockach). All other municipalities use a single, region-wide collection schedule and don't need this.

**range_selector**
*(string) (optional)*

Only needed for the small number of streets that are split into several house-number based collection areas (for example, one side of the street is collected on a different schedule than the other). Leave this empty at first — if it is required, the resulting error message will list all valid values for your street so you can copy the correct one.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: muellmann_app_de
      args:
        city: Aach
```

```yaml
waste_collection_schedule:
  sources:
    - name: muellmann_app_de
      args:
        city: Radolfzell
        street: Mooser Straße
```
