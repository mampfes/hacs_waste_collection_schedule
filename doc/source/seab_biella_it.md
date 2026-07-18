# SEAB Biella

Support for schedules provided by [SEAB Biella](https://www.seab.biella.it).

Source for SEAB Biella (Italy) waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: seab_biella_it
      args:
        url: URL
```

### Configuration Variables

**url**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: seab_biella_it
      args:
        url: https://www.seab.biella.it/wp-content/uploads/2026/05/Ailoche-II-semestre.pdf
```

## How to get the source arguments

Visit https://www.seab.biella.it/aree-servite, select your municipality and copy the link to the PDF calendar file.
