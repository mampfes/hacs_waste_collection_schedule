# Mulhouse Alsace Agglomération (m2A)

Support for door-to-door household waste collection schedules in [Mulhouse
Alsace Agglomération](https://www.mulhouse-alsace.fr/), based on the
[official open data portal](https://data.mulhouse-alsace.fr/).

The dataset covers all 39 municipalities of the agglomeration. For Mulhouse
itself, the schedule depends on the district (quartier) — pick the one
matching your home.

## Configuration via `configuration.yaml`

```yaml
waste_collection_schedule:
    sources:
    - name: mulhouse_alsace_fr
      args:
        commune: COMMUNE
        quartier: QUARTIER  # only required for Mulhouse
```

### Configuration Variables

**commune**  
*(String) (required)*

Name of the m2A municipality (e.g. `Wittelsheim`, `Habsheim`, `Mulhouse`).

**quartier**  
*(String) (optional)*

District inside Mulhouse (e.g. `Centre Ville`, `Rebberg`, `Bourtzwiller`).
Required when `commune: Mulhouse`. Ignored for other municipalities.

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: mulhouse_alsace_fr
      args:
        commune: Wittelsheim
```

```yaml
waste_collection_schedule:
    sources:
    - name: mulhouse_alsace_fr
      args:
        commune: Mulhouse
        quartier: Rebberg
```

## How to get the source arguments

Visit the dataset page at
[data.mulhouse-alsace.fr](https://data.mulhouse-alsace.fr/explore/dataset/m2a_collecte-en-porte-a-porte-des-dechets-menagers_m2a/table/)
and look up your municipality. The `com_nom` column gives the value to use
for `commune`. For Mulhouse, the `quartier` column lists the available
districts.

## Notes

- Collection dates are projected from the official frequency and weekday
  rules published in the dataset, then adjusted using the `ferie` field
  (public-holiday reschedules and cancellations).
- The four streams returned (when applicable to your municipality) are:
  *Ordures ménagères*, *Tri sélectif*, *Bio-déchets*, *Déchets verts*.
