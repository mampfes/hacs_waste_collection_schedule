# Mühlenkreis Minden-Lübbecke

Support for schedules provided by [Mühlenkreis Minden-Lübbecke](https://www.muehlenkreis.de), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: muehlenkreis_de
      args:
        strasse: STRASSE
        ort: ORT
```

### Configuration Variables

**strasse**
*(string) (required)*

Street name (or a unique partial match), as offered by the autocomplete on the Abfallkalender page.

**ort**
*(string) (optional)*

Place, used to disambiguate streets that exist in more than one location (the part shown in parentheses, e.g. `Harlinghausen`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: muehlenkreis_de
      args:
        strasse: "Hauptstraße"
        ort: "Harlinghausen"
```

## How to get the source arguments

1. Go to [Abfallkalender Mühlenkreis](https://www.muehlenkreis.de/iKISS-Start/Mitteilungen/Abfallkalender-2024.php).
2. Start typing your street name and pick it from the suggestions.
3. Use the street name as `strasse`. If the same street exists in several places, add the place shown in parentheses as `ort`.
