# Oberndorf bei Schwanenstadt

Support for schedules provided by [Oberndorf bei Schwanenstadt](https://www.oberndorf.ooe.gv.at).

Source for Oberndorf bei Schwanenstadt waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: oberndorf_schwanenstadt_at
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
    - name: oberndorf_schwanenstadt_at
      args:
        strasse: Am Hang
        hausnummer: '2'
```

## How to get the source arguments

Visit https://www.oberndorf.ooe.gv.at, pick your street and house number from the waste-calendar dropdowns on the homepage, and use the same values here.
