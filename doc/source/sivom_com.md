# SIVOM de la Vallée de l'Yerres et des Sénarts

Support for schedules provided by [SIVOM de la Vallée de l'Yerres et des Sénarts](https://www.sivom.com), serving the following communes in the Seine-et-Marne and Essonne departments (Île-de-France), France:

- Boussy-Saint-Antoine
- Brie-Comte-Robert
- Brunoy
- Combs-la-Ville
- Crosne
- Épinay-sous-Sénart
- Mandres-les-Roses
- Marolles-en-Brie
- Moissy-Cramayel
- Périgny-sur-Yerres
- Quincy-sous-Sénart
- Santeny
- Varennes-Jarcy
- Villecresnes
- Yerres

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: sivom_com_fr
      args:
        commune: COMMUNE
        street: STREET
```

### Configuration Variables

**commune**
*(String) (required)*

Name of the commune (upper-case), e.g. `VILLECRESNES`, `BRUNOY`, `YERRES`.

**street**
*(String) (required)*

Name of the street as shown on the SIVOM website, e.g. `ACACIAS Allée des`.

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: sivom_com_fr
      args:
        commune: VILLECRESNES
        street: ACACIAS Allée des
```

```yaml
waste_collection_schedule:
    sources:
    - name: sivom_com_fr
      args:
        commune: BRUNOY
        street: ABBAYE rue de l
```

```yaml
waste_collection_schedule:
    sources:
    - name: sivom_com_fr
      args:
        commune: YERRES
        street: ABBAYE avenue de l'
```

## How to get the source arguments

1. Visit [https://www.sivom.com/mesjoursdecollectes/?v=YOUR_COMMUNE](https://www.sivom.com/mesjoursdecollectes/) (replace `YOUR_COMMUNE` with the upper-case name of your commune, e.g. `VILLECRESNES`).
2. Find your street in the list displayed on the page.
3. Use the commune name and street name exactly as shown on the site.

## Waste types

The source returns up to three collection types:

| Type | Description |
|------|-------------|
| Bac vert (Résiduels) | Residual / non-recyclable household waste (green bin) |
| Bac jaune (Emballages) | Recyclable packaging (yellow bin) |
| Bac marron (Végétaux) | Garden / green waste (brown bin) — collected approximately March 15 to December 14 |
