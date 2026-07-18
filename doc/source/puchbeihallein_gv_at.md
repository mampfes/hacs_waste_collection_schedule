# Puch bei Hallein

Support for schedules provided by [Puch bei Hallein](https://www.puchbeihallein.gv.at).

Waste collection schedule for Puch bei Hallein, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: puchbeihallein_gv_at
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
    - name: puchbeihallein_gv_at
      args:
        strasse: "Ahornstra\xDFe"
        hausnummer: '3'
```

## How to get the source arguments

Visit https://www.puchbeihallein.gv.at/Buergerservice/Aktuelles/Abfallkalender, pick your street and house number from the dropdowns, and use the same values for 'strasse' and 'hausnummer'.
