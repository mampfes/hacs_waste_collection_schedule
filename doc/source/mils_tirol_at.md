# Gemeinde Mils

Support for schedules provided by [Gemeinde Mils](https://mils-tirol.at).

Source for Gemeinde Mils, Tyrol, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mils_tirol_at
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
    - name: mils_tirol_at
      args:
        strasse: Fichtenweg
        hausnummer: '21'
```

## How to get the source arguments

Open https://mils-tirol.at/Service/Dienstleistungen/Abfallkalender, pick your street and house number from the dropdowns, and use the same values for 'strasse' and 'hausnummer'.
