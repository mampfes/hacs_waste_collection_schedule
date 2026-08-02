# Omrin

Support for waste collection schedules provided by [Omrin](https://www.omrin.nl)
in the municipalities of Achtkarspelen, Ameland, Eemsdelta, Elburg, Ermelo,
Harderwijk, Harlingen, Heerenveen, Het Hogeland, Leeuwarden, Nunspeet,
Oldebroek, Ooststellingwerf, Opsterland, Pekela, Schiermonnikoog, Terschelling,
Tytsjerksteradiel, Waadhoeke, Westerwolde, and Weststellingwerf.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: omrin_nl
      args:
        postal_code: POSTAL_CODE
        house_number: HOUSE_NUMBER
        suffix: HOUSE_NUMBER_SUFFIX  # optional
```

### Configuration Variables

**postal_code**
*(string) (required)*

Dutch postal code, for example `3851LJ`.

**house_number**
*(string | integer) (required)*

House number.

**suffix**
*(string) (optional)*

House number suffix, if applicable.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: omrin_nl
      args:
        postal_code: "3851LJ"
        house_number: "4"
```
