# Ville de Chambly

Support for schedules provided by [Ville de Chambly](https://espacechambly.ca).

Source for the Ville de Chambly (Québec) collection calendars.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: chambly_ca
      args:
        secteur: SECTEUR
```

### Configuration Variables

**secteur**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: chambly_ca
      args:
        secteur: '1'
```

## How to get the source arguments

Find your collection sector (1 to 4) on the sector map linked from https://espacechambly.ca/info-collecte and choose it.
