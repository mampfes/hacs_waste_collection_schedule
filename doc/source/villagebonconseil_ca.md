# Notre-Dame-du-Bon-Conseil (Village)

Support for schedules provided by [Village de Notre-Dame-du-Bon-Conseil](https://villagebonconseil.ca).

## Configuration via GUI

1. Add "Waste Collection Schedule" integration
2. Select "Notre-Dame-du-Bon-Conseil (Village)" as the source
3. No configuration required - same schedule for all residents

## Configuration via YAML

```yaml
waste_collection_schedule:
  sources:
    - name: villagebonconseil_ca
      args:
```

No arguments required - the calendar is the same for all residents.

## Waste Types

- **Ordures ménagères** (Household waste) - `mdi:trash-can`
- **Matières organiques** (Organic waste) - `mdi:leaf`
- **Matières recyclables** (Recyclables) - `mdi:recycle`
- **Conteneur en métal – Déchets** (Metal container waste) - `mdi:factory`
- **Conteneur en métal – Recyclage** (Metal container recycling) - `mdi:recycle`
- **Encombrants** (Bulky items) - `mdi:sofa`
