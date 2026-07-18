# Neunkirchen Siegerland

Support for schedules provided by [Neunkirchen Siegerland](https://www.neunkirchen-siegerland.de).

Source for 'Abfallkalender Neunkirchen Siegerland'.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_neunkirchen_siegerland_de
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
    - name: abfall_neunkirchen_siegerland_de
      args:
        strasse: Waldstr
```

## How to get the source arguments

Enter a partial or full street name as shown on the Neunkirchen Siegerland waste calendar (e.g. 'Waldstr' for 'Waldstraße'). If the street exists in several districts, add the district (Ortsteil) shown in parentheses (e.g. 'Neunkirchen').
