# Stadtbetriebe Steyr GmbH

Support for schedules provided by [Stadtbetriebe Steyr GmbH](https://www.steyr.at).

Source for Stadtbetriebe Steyr GmbH waste collection schedule.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: steyr_at
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
    - name: steyr_at
      args:
        strasse: "Wolfernstra\xDFe"
        hausnummer: '7'
```
