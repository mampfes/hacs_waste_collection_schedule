# AJL - Abfallwirtschaftsgesellschaft Jerichower Land mbH

Support for schedules provided by [AJL - Abfallwirtschaftsgesellschaft Jerichower Land mbH](https://www.ajl-mbh.de), serving the Jerichower Land district in Saxony-Anhalt, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: ajl_mbh_de
      args:
        town: TOWN
        street: STREET  # optional — only required for towns with multiple collection zones
```

### Configuration Variables

**town**  
*(String | Integer) (required)*

The name of your town (e.g. `Biederitz`) or its numeric ID as shown in the URL on the collection calendar page.

**street**  
*(String | Integer) (optional)*

The street name (e.g. `Fliederweg`) or its numeric ID. Only required for larger towns where the collection schedule differs by street. If omitted and the town has multiple collection zones, an error listing the available streets will be raised.

## Example — town without street filter

```yaml
waste_collection_schedule:
    sources:
    - name: ajl_mbh_de
      args:
        town: Biederitz
```

## Example — town with street filter

```yaml
waste_collection_schedule:
    sources:
    - name: ajl_mbh_de
      args:
        town: Burg
        street: Fliederweg
```

## How to get the source arguments

1. Open the [AJL collection calendar](https://www.ajl-mbh.de/abfallkalender/entsorgungstermine).
2. Click your town from the alphabetical list. The URL will contain `town=<ID>`.
3. If a street dropdown appears, select your street. The URL will then also contain `street=<ID>`.
4. Use the town and street names (or numeric IDs) as the `town` and `street` arguments.
