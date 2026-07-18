# Stadt Hilchenbach

Support for schedules provided by [Stadt Hilchenbach](https://www.hilchenbach.de).

Source for 'Abfallkalender Stadt Hilchenbach'.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hilchenbach_de
      args:
        strasse: STRASSE
        ort: ORT
```

### Configuration Variables

**strasse**  
*(string) (required)*

**ort**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hilchenbach_de
      args:
        strasse: Dammstr
```

## How to get the source arguments

Street name or a unique part of it. Optionally add the district (the part in parentheses, e.g. 'Allenbach') to disambiguate.
