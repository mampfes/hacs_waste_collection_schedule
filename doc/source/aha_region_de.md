# Zweckverband Abfallwirtschaft Region Hannover

Support for schedules provided by [Zweckverband Abfallwirtschaft Region Hannover](https://www.aha-region.de/).

Source for Zweckverband Abfallwirtschaft Region Hannover.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: aha_region_de
      args:
        gemeinde: GEMEINDE
        strasse: STRASSE
        hnr: HNR
        zusatz: ZUSATZ
        ladeort: LADEORT
```

### Configuration Variables

**gemeinde**  
*(string) (required)*

**strasse**  
*(string) (required)*

**hnr**  
*(string) (required)*

**zusatz**  
*(string) (optional)*

**ladeort**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: aha_region_de
      args:
        gemeinde: Neustadt a. Rbge.
        strasse: "Am Rotdorn / N\xF6pke"
        hnr: 1
```
