# Micheldorf in Oberösterreich

Support for schedules provided by [Micheldorf in Oberösterreich](https://www.micheldorf.at).

Source for Micheldorf in Oberösterreich, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: micheldorf_at
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
    - name: micheldorf_at
      args:
        strasse: "Adalbert-Stifter-Stra\xDFe"
        hausnummer: '1'
```
