# Heimat-Info

Support for schedules provided by [Heimat-Info](https://www.heimat-info.de).

Source for Heimat-Info (heimat-info.de) waste collection schedules.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: heimat_info_de
      args:
        commune: COMMUNE
        area: AREA
```

### Configuration Variables

**commune**  
*(string) (required)*

**area**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: heimat_info_de
      args:
        commune: gruendau
        area: Breitenborn
```

## How to get the source arguments

Open https://www.heimat-info.de, search for your commune, and navigate to Abfallkalender. The commune slug is the part of the URL after '/gemeinden/'. If the calendar shows multiple collection areas, pick yours from the list.
