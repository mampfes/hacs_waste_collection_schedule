# SICTOM du Val de Saône

Support for [SICTOM du Val de Saône](https://www.sictomvds.com) waste collection schedules in Haute-Saône (70), France.

Schedules are fetched live from the SICTOM interactive map (commune → PDF lookup) — no hardcoded dates.

## Configuration via YAML

```yaml
waste_collection_schedule:
  sources:
    - name: sictomvds_com
      args:
        commune: Velleminfroy
```

## Configuration via UI

| Parameter | Type   | Required | Description |
|-----------|--------|----------|-------------|
| commune   | string | yes      | Name of the municipality as shown on the SICTOM map (e.g. `Velleminfroy`, `Ancier`, `Mantoche`). Case-insensitive, accents optional. |

## Notes

- Covers ~266 communes served by SICTOM Val de Saône.
- Two waste streams are returned: **Ordures ménagères** (general waste) and **Tri** (recyclables).
- Glass collection is drop-off only and is not included.
- Collection days shift by +1 day for 1 January, 1 May, and 25 December only; all other public holidays are collected as normal.
