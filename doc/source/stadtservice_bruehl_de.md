# StadtService Brühl

Support for schedules provided by [StadtService Brühl](https://services.stadtservice-bruehl.de/abfallkalender/), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stadtservice_bruehl_de
      args:
        strasse: STRASSE
        hnr: Hausnummer
```

### Configuration Variables

**strasse**<br>
*(string) (required)*
**hnr**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stadtservice_bruehl_de
      args:
        strasse: "Badorfer Straße"
        hnr: "1"

```

## How to get the source arguments

1. Go to your calendar at [StadtService Brühl - Abfallkalender](https://services.stadtservice-bruehl.de/abfallkalender/)
2. Enter your street and housenumber
3. Copy the exact values from the textboxes street in the source configuration.