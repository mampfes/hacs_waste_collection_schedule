# Imst

Support for schedules provided by [Imst](https://www.imst.gv.at).

Waste collection schedule for Stadtgemeinde Imst, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: imst_at
      args:
        strasse: STRASSE
        hausnummer: HAUSNUMMER
```

### Configuration Variables

**strasse**  
*(string) (required)*

**hausnummer**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: imst_at
      args:
        strasse: Auf Arzill
        hausnummer: '154'
```

## How to get the source arguments

Open https://www.imst.gv.at/Muellabfuhrplaene_1, pick your street and house number from the dropdowns, and use the same values for 'strasse' and 'hausnummer'.
