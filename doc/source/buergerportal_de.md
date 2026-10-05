# Bürgerportal

Support for schedules provided by [Bürgerportal](https://www.c-trace.de).

Source for waste collection in multiple c-trace Bürgerportal service areas.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: buergerportal_de
      args:
        operator: OPERATOR
        district: DISTRICT
        subdistrict: SUBDISTRICT
        street: STREET
        number: NUMBER
```

### Configuration Variables

**operator**  
*(string) (required)*

**district**  
*(string) (required)*

**subdistrict**  
*(string) (optional)*

**street**  
*(string) (required)*

**number**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: buergerportal_de
      args:
        operator: cochem_zell
        district: Bullay
        subdistrict: Bullay
        street: Layenweg
        number: 3
```

## How to get the source arguments

1. Open your operator's Bürgerportal and select 'Abfuhrkalender'.
2. Choose your district (Ort). If it contains a comma (e.g. 'Bullay, Bullay'), split it: the part before the comma is `district`, the part after is `subdistrict` — even if both parts are identical. Leave `subdistrict` empty only if there is no comma.
3. Choose your street and house number.
