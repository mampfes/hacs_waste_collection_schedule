# Montpellier Méditerranée Métropole

Support for waste collection schedules provided by [Montpellier Méditerranée Métropole](https://data.montpellier3m.fr) via their open data portal.

Covers 31 communes including Montpellier, Lattes, Castelnau-le-Lez, Juvignac, Pérols, Clapiers, Grabels, Saint-Jean-de-Védas, and more.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: data_montpellier3m_fr
      args:
        street_name: STREET_NAME
        house_number: HOUSE_NUMBER  # optional
        commune: COMMUNE            # optional
```

### Configuration Variables

**street_name**
*(string) (required)*

Your full street name using standard French spelling, e.g. `Rue Parlier`, `Avenue de Montpellier`, `Chemin des Prés`. Abbreviations used in the dataset (R, AV, CHE, etc.) are automatically expanded.

**house_number**
*(integer or string) (optional)*

Your house number. Recommended for accurate results on streets where collection days vary by odd/even side.

**commune**
*(string) (optional)*

The commune name in upper case, e.g. `MONTPELLIER`, `LATTES`, `CASTELNAU-LE-LEZ`. Required if the same street name exists in multiple communes.

## How to get the source arguments

1. Find your street name and commune on [Montpellier's waste collection page](https://www.montpellier.fr/vie-quotidienne/vivre-ici/gerer-ses-dechets/jours-de-collecte-des-dechets-et-points-apport-volontaire).
2. Use your street name (full spelling) and optionally your house number.

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: data_montpellier3m_fr
      args:
        street_name: "Rue Parlier"
        house_number: 3
        commune: "MONTPELLIER"
```
