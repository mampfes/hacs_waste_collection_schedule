# Grand Paris Sud Est Avenir (GPSEA)

Support for waste collection schedules provided by [Grand Paris Sud Est Avenir (GPSEA)](https://sudestavenir.fr/), an intercommunal territory in the Val-de-Marne department of France, serving the following communes:

- Alfortville
- Boissy-Saint-Léger
- Bonneuil-sur-Marne
- Chennevières-sur-Marne
- Créteil
- Limeil-Brévannes
- Noiseau
- Ormesson-sur-Marne
- Le Plessis-Trévise
- La Queue-en-Brie
- Sucy-en-Brie

Collection days depend on the exact address (commune, street and house number) and are looked up live against GPSEA's interactive collection map.

Depending on the waste type and address, the source returns either a recurring weekly/bi-weekly schedule (ordures ménagères, emballages) or a precomputed list of dates for the current calendar year (verre, encombrants, déchets végétaux), matching what the source website itself provides.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: sudestavenir_fr
      args:
        commune: Creteil
        street: Place du Grand Pavois
        house_number: 1
```

### Configuration Variables

**commune**
*(String) (required)*

Your commune within the GPSEA territory.

**street**
*(String) (required)*

Your street name.

**house_number**
*(String) (required)*

Your house number.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: sudestavenir_fr
      args:
        commune: Creteil
        street: Place du Grand Pavois
        house_number: 1
```

## How to get the source argument

Visit [https://sudestavenir.fr/](https://sudestavenir.fr/) and use the "Où jeter ?" / collection map to look up your commune, street and house number, or simply provide the same address details you would type into that map's search box.
