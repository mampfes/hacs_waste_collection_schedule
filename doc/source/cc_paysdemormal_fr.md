# Communauté de Communes du Pays de Mormal

Support for schedules provided by [Communauté de Communes du Pays de Mormal](https://www.cc-paysdemormal.fr).

Source for the Pays de Mormal (Nord) collection calendars, France.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cc_paysdemormal_fr
      args:
        commune: COMMUNE
        semaine: SEMAINE
```

### Configuration Variables

**commune**  
*(string) (required)*

**semaine**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cc_paysdemormal_fr
      args:
        commune: Frasnoy
```

## How to get the source arguments

Enter your commune as listed on https://www.cc-paysdemormal.fr/calendriers-de-collecte/. In Bavay, La Longueville, Landrecies, Le Quesnoy and Poix-du-Nord the packaging (bac de tri) week depends on your street: look it up on the map of the calendar and set `semaine` to `paire` (even weeks) or `impaire` (odd weeks). Leave it empty elsewhere.
