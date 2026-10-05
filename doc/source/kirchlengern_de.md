# Gemeinde Kirchlengern

Support for schedules provided by [Gemeinde Kirchlengern](https://www.kirchlengern.de).

Source for Gemeinde Kirchlengern, Germany, waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kirchlengern_de
      args:
        strasse: STRASSE
```

### Configuration Variables

**strasse**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kirchlengern_de
      args:
        strasse: Alter Postweg
```

## How to get the source arguments

Enter your street name exactly as it appears in the waste calendar tool on the Kirchlengern website (Bürgerservice → Abfallkalender/Abfallberatung). If the street is not found, the error message lists all valid street names.
