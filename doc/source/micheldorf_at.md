# Micheldorf in Oberösterreich

Support for waste collection schedules provided by [Marktgemeinde Micheldorf in Oberösterreich](https://www.micheldorf.at), Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: micheldorf_at
      args:
        strasse: STREET
        hausnummer: HOUSE_NUMBER
```

### Configuration Variables

**strasse**
*(string) (required)*

Street name as listed in the Micheldorf waste calendar dropdown (case-insensitive).

**hausnummer**
*(string | integer) (required)*

House number as listed in the Micheldorf waste calendar dropdown.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: micheldorf_at
      args:
        strasse: "Adalbert-Stifter-Straße"
        hausnummer: "1"
```

## How to get the source arguments

Open <https://www.micheldorf.at/system/web/kalender.aspx?sprache=1&menuonr=227975509>, choose your street and house number from the dropdowns, and use the same values for `strasse` and `hausnummer`.
