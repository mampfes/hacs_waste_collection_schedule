# Gemeinde Bürmoos

Support for schedules provided by [Gemeinde Bürmoos](https://www.buermoos.at).

Source for Gemeinde Bürmoos, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: buermoos_at
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
    - name: buermoos_at
      args:
        strasse: "Birkenstra\xDFe"
        hausnummer: 76a
```

## How to get the source arguments

Open https://www.buermoos.at/Service/Aktuelles/Muellkalender, pick your street and house number from the dropdowns, and use the same values for 'strasse' and 'hausnummer'.
