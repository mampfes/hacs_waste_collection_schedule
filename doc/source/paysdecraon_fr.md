# Communauté de Communes du Pays de Craon

Support for schedules provided by the [Communauté de Communes du Pays de Craon](https://www.paysdecraon.fr/environnement/dechets-et-dechetteries/) (Mayenne, France), which serves Saint-Michel-de-la-Roë, Craon, Renazé, Cossé-le-Vivien and the other member municipalities.

The source downloads the yearly *Calendrier de collecte* PDF published by the Pays de Craon. The calendar marks every week as an *Ordures Ménagères* (household waste) week or an *Emballages* (packaging) week. Your bin is collected on your usual weekday in that week. After a public holiday, the collection is moved to the next day, as stated in the calendar.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: paysdecraon_fr
      args:
        weekday: WEEKDAY
        commune: COMMUNE
```

### Configuration Variables

**weekday**
*(String) (required)*

The weekday on which your bins are usually collected: `lundi`, `mardi`, `mercredi`, `jeudi` or `vendredi`. The English names (`monday` … `friday`) also work.

**commune**
*(String) (optional)*

Your municipality, e.g. `Saint-Michel-de-la-Roë`. If you set it, the source also returns your municipality's *Broyage de branches* (branch shredding) date. If you leave it out, the source only returns the household waste and packaging collections.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: paysdecraon_fr
      args:
        weekday: mercredi
        commune: Saint-Michel-de-la-Roë
```

## How to get the source arguments

Use the weekday on which your bins (grey/bordeaux lid for household waste, yellow lid for packaging) are usually collected. If you are not sure, contact the Pays de Craon environment service (02 43 09 61 64, environnement@paysdecraon.fr). The municipality name must match the name printed in the [collection calendar](https://www.paysdecraon.fr/environnement/dechets-et-dechetteries/). Accents, hyphens and `Saint`/`St` spellings don't matter.
