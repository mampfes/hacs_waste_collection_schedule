# RITL (Régie intermunicipale des Trois-Lacs)

Support for waste collection schedules managed by the [Régie intermunicipale des Trois-Lacs (RITL)](https://ritl.ca/) in the Laurentides region of Quebec, Canada.

This source covers the following municipalities:
- Ivry-sur-le-Lac
- Lac-Supérieur (Secteur 1, Secteur 2)
- Lantier
- Montcalm (Secteur 1)
- Mont-Blanc (Secteur Est, Secteur Ouest)
- Sainte-Agathe-des-Monts (Secteur Centre-ville, Secteur Nord, Secteur Sud / Fatima)
- Sainte-Lucie-des-Laurentides
- Val-des-Lacs
- Val-David (Secteur 1, Secteur 2, Secteur 3)
- Val-Morin (Val-Morin Est, Val-Morin Ouest)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ritl_ca
      args:
        municipality: MUNICIPALITY
        sector: SECTOR
```

### Configuration Variables

**municipality**<br>
*(string) (required)*<br>
The name of your municipality. E.g., `Lac-Supérieur`, `Val-David`, `Ivry-sur-le-Lac`.

**sector**<br>
*(string) (optional)*<br>
The name of your sector. Only required if the municipality is divided into sectors. E.g., `Secteur 1`, `Secteur Est`, `Val-Morin Ouest`.

## Examples

### Lac-Supérieur Secteur 1
```yaml
waste_collection_schedule:
  sources:
    - name: ritl_ca
      args:
        municipality: Lac-Supérieur
        sector: Secteur 1
```

### Val-David Secteur 2
```yaml
waste_collection_schedule:
  sources:
    - name: ritl_ca
      args:
        municipality: Val-David
        sector: Secteur 2
```

### Ivry-sur-le-Lac (no sector needed)
```yaml
waste_collection_schedule:
  sources:
    - name: ritl_ca
      args:
        municipality: Ivry-sur-le-Lac
```
