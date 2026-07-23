# Syndicat Emeraude (France)

This source provides waste collection schedules for municipalities managed by the Syndicat Emeraude in the Val-d’Oise (Île-de-France, France).

It supports multiple communes and sectors.

## Supported Communes

- Andilly
- Deuil-la-Barre
- Eaubonne
- Enghien-les-Bains
- Ermont
- Franconville
- Groslay
- Le Plessis-Bouchard
- Margency
- Montigny
- Montlignon
- Montmagny
- Montmorency
- Saint-Prix
- Saint-Gratien
- Sannois
- Soisy-sous-Montmorency

## Configuration example

```yaml
waste_collection_schedule:
  sources:
    - name: syndicat_emeraude_fr
      args:
        commune: montmorency
        sector: pavillons
```

## Arguments

commune (string, required)
Name of the commune in lowercase.

sector (string, optional)
Default: pavillons

Possible values:
- pavillons
- collectifs
- ville (Only Enghien-les-Bains)
- hypercentre (Only Enghien-les-Bains)

## Features

- All communes under "Syndicat Emeraude" supported
- Different rules per sector
- Weekly and monthly schedules
- Seasonal collections (e.g. végétaux)
- Mid-month collection logic

## Waste types

Ordures ménagères → 🗑️  
Papiers/Emballages → ♻️  
Verre → 🍾  
Végétaux → 🌿  
Encombrants → 🪑  

## Notes

Schedules are generated from January 1st of the current year to 2 years ahead.

Some communes do not have all waste types.

Rules differ significantly between pavillons and collectifs.

## Test cases

All test cases are covered :
ANDILLY_PAVILLONS
ANDILLY_COLLECTIFS
DEUIL-LA-BARRE_PAVILLONS
DEUIL-LA-BARRE_COLLECTIFS
EAUBONNE_PAVILLONS
EAUBONNE_COLLECTIFS
ENGHIEN-LES-BAINS_VILLE
ENGHIEN-LES-BAINS_HYPERCENTRE
ERMONT_PAVILLONS
ERMONT_COLLECTIFS
FRANCONVILLE_PAVILLONS
FRANCONVILLE_COLLECTIFS
GROSLAY_PAVILLONS
GROSLAY_COLLECTIFS
LE-PLESSIS-BOUCHARD_PAVILLONS
LE-PLESSIS-BOUCHARD_COLLECTIFS
MARGENCY_PAVILLONS
MARGENCY_COLLECTIFS
MONTIGNY_PAVILLONS
MONTIGNY_COLLECTIFS
MONTLIGNON_PAVILLONS
MONTLIGNON_COLLECTIFS
MONTMAGNY_PAVILLONS
MONTMAGNY_COLLECTIFS
MONTMORENCY_PAVILLONS
MONTMORENCY_COLLECTIFS
SAINT-PRIX_PAVILLONS
SAINT-PRIX_COLLECTIFS
SAINT-GRATIEN_PAVILLONS
SAINT-GRATIEN_COLLECTIFS
SANNOIS_PAVILLONS
SANNOIS_COLLECTIFS
SOISY-SOUS-MONTMORENCY_PAVILLONS
SOISY-SOUS-MONTMORENCY_COLLECTIFS
