# Kurstadt Bad Orb

Support for schedules provided by [Kurstadt Bad Orb](https://stadt-bad-orb.de).

Source for Kurstadt Bad Orb waste collection.

## Configuration via configuration.yaml

### Using strasse

```yaml
waste_collection_schedule:
  sources:
    - name: stadt_bad_orb_de
      args:
        strasse: STRASSE
```

### Using pois

```yaml
waste_collection_schedule:
  sources:
    - name: stadt_bad_orb_de
      args:
        pois: POIS
```

### Configuration Variables

**strasse**  
*(string) (alternative)*

**pois**  
*(string) (alternative)*

Provide one of: `strasse` or `pois`.

## Example

### Using strasse

```yaml
waste_collection_schedule:
  sources:
    - name: stadt_bad_orb_de
      args:
        strasse: "Kurparkstra\xDFe"
```

### Using pois

```yaml
waste_collection_schedule:
  sources:
    - name: stadt_bad_orb_de
      args:
        pois: '3157.157'
```

## How to get the source arguments

Enter your street as listed in the Abfalltourenmodul on stadt-bad-orb.de, or the `pois` value from the page's URL after selecting your street (e.g. 3157.194).
