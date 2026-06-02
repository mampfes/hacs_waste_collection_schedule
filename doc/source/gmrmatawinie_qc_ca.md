# MRC Matawinie (QC)

This source provides waste collection schedules for the MRC de Matawinie region in Quebec, Canada.

## Configuration

### Configuration File

```yaml
waste_collection_schedule:
  sources:
    - name: gmrmatawinie_qc_ca
      args:
        city_id: Saint-Alphonse-Rodriguez
```

### Configuration Examples

##### Basic

```yaml
waste_collection_schedule:
  sources:
    - name: gmrmatawinie_qc_ca
      args:
        city_id: Saint-Alphonse-Rodriguez
```

##### With all entries

```yaml
waste_collection_schedule:
  sources:
    - name: gmrmatawinie_qc_ca
      args:
        city_id: Saint-Alphonse-Rodriguez
```

## How to Find Your Sector

1. Visit the [MRC Matawinie collection calendar](https://gmrmatawinie.org/calendriers-collectes/)
2. Find your municipality and sector
3. Select your sector from the dropdown list

## Supported Municipalities and Sectors

| Municipality/Sector |
|---------------------|
| Sainte-Émélie-de-l'Énergie |
| Saint-Zénon |
| Saint-Côme |
| Saint-Alphonse-Rodriguez |
| Saint-Damien |
| Saint-Jean-de-Matha |
| Saint-Félix-de-Valois |
| Sainte-Béatrix |
| Sainte-Marcelline-de-Kildare |
| Saint-Côme - Secteur Lac Côme |
| Saint-Jean-de-Matha - Secteurs rangs St-François et Sacré-Coeur, St-Guillaume, lac Mondor, Pointe du lac Noir |
| Saint-Alphonse-Rodriguez - Secteurs lac des Français et lac Cloutier |
| Sainte-Béatrix - Secteurs de la Montagne (Montée St-Jacques, rue du Moulin et rue Panoramique) et Petit Beloeil |
| Sainte-Émélie-de-l'Énergie - Secteurs Lac Noir et Crique à David |
| Saint-Jean-de-Matha - Secteur Chemin du Golf |
| Saint-Damien - Secteur Chemin de la Montagne |
| Saint-Damien - Secteur Les Cèdres du Liban |
