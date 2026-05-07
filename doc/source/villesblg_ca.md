# Ville de Saint-Basile-le-Grand (QC)

Support for schedules provided by [Ville de Saint-Basile-le-Grand](https://www.villesblg.ca).

## Configuration via GUI

1. Add "Waste Collection Schedule" integration
2. Select "Ville de Saint-Basile-le-Grand" as the source
3. No configuration required - same schedule for all residents

## Configuration via YAML

```yaml
waste_collection_schedule:
  sources:
    - name: villesblg_ca
      args:
```

No arguments required - the calendar is the same for all residents of Saint-Basile-le-Grand.

## Waste Types

- **Ordures** (Trash) - `mdi:trash-can`
- **Matières récupérables** (Recycling) - `mdi:recycle`
- **Résidus verts** (Green waste) - `mdi:leaf`
- **Résidus alimentaires** (Food waste) - `mdi:food-apple`
- **Encombrants** (Bulky items) - `mdi:sofa`

Note: Events titled "Dépôt de rebuts encombrants et récupérables" and "Dépôt de résidus domestiques dangereux (RDD)" are skipped as they are not regular collection events.
