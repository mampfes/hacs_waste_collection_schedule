# Hart bei Graz

Support for waste collection schedules provided by [Gemeinde Hart bei Graz](https://www.hartbeigraz.at), Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hartbeigraz_at
      args:
        strasse: STREET
        hausnummer: HOUSE_NUMBER
```

### Configuration Variables

**strasse**
*(string) (required)*

Street name as listed in the Hart bei Graz waste calendar dropdown (case-insensitive).

**hausnummer**
*(string | integer) (required)*

House number as listed in the Hart bei Graz waste calendar dropdown.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hartbeigraz_at
      args:
        strasse: "Am Brühlwald"
        hausnummer: "15"
```

## How to get the source arguments

Open <https://www.hartbeigraz.at/Service/Muell>, pick your street and house number from the dropdowns, and use the same values for `strasse` and `hausnummer`.
