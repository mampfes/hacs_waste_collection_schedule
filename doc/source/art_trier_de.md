# A.R.T. Trier (Deprecated)

Support for schedules provided by [A.R.T. Trier (Deprecated)](https://www.art-trier.de).

Source for waste collection of A.R.T. Trier.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: art_trier_de
      args:
        zip_code: ZIP_CODE
        district: DISTRICT
```

### Configuration Variables

**zip_code**  
*(string) (required)*

**district**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: art_trier_de
      args:
        zip_code: '54296'
        district: "Stadt Trier, Universit\xE4tsring"
```
