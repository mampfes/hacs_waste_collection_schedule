# Ximmio

Support for schedules provided by [Ximmio](https://www.ximmio.nl) (Netherlands).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ximmio_nl
      args:
        company: COMPANY
        post_code: POSTAL_CODE
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**company**
*(string) (required)*

Short name identifying your waste collection provider. See supported companies below.

**post_code**
*(string) (required)*

Your postal code (e.g. `3441AX`).

**house_number**
*(string or integer) (required)*

Your house number.

## Supported Companies

| Title | company |
|---|---|
| ACV Group | `acv` |
| Gemeente Almere | `almere` |
| Area Afval | `areareiniging` |
| Avalex | `avalex` |
| Avri | `avri` |
| Bar Afvalbeheer | `bar` |
| Gemeente Hellendoorn | `hellendoorn` |
| Meerlanden | `meerlanden` |
| Gemeente Meppel | `meppel` |
| Mijn Blink | `mijnblink` |
| RAD BV | `rad` |
| Twente Milieu | `twentemilieu` |
| Waardlanden | `waardlanden` |
| Gemeente Westland | `westland` |
| Gemeente Venlo | `venlo` |
| Woerden / Oudewater | `woerdenoudewater` |

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ximmio_nl
      args:
        company: woerdenoudewater
        post_code: 3441AX
        house_number: 1
```
