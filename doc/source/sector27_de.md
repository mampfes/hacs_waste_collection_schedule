# Sector 27 - Datteln, Marl, Oer-Erkenschwick

Support for schedules provided by [Sector 27 - Datteln, Marl, Oer-Erkenschwick](https://muellkalender.sector27.de).

Source for Muellkalender in Kreis RE.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sector27_de
      args:
        city: CITY
        street: STREET
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sector27_de
      args:
        city: Datteln
        street: Am Bahnhof
```

## How to get the source arguments

Choose Datteln, Marl or Oer-Erkenschwick and enter your street exactly as it is listed on https://muellkalender.sector27.de (for split streets including the house number range, e.g. 'Ahsener Straße 113 - 161 (ungerade)').
