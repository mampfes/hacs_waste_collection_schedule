# Technische Betriebe Velbert

Support for schedules provided by [Technische Betriebe Velbert](https://www.tbv-velbert.de/), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tbv_velbert_de
      args:
        street: STRASSE
```

### Configuration Variables

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: tbv_velbert_de
      args:
        strasse: "Am Lindenkamp 33"

```

## How to get the source arguments

1. Go to your calendar at [TBV Velbert - Abfalltermine](https://www.tbv-velbert.de/abfall/abfallkalender-und-abfuhrtermine/abfallabfuhr-suche)
2. Enter your street.
3. Copy the exact values from the textboxes street in the source configuration. 

*IMPORTANT* - the string as strasse must match only 1 entry
