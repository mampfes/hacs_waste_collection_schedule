# tonnenleerung.de LK Aichach-Friedberg + Neuburg-Schrobenhausen

Support for schedules provided by [tonnenleerung.de LK Aichach-Friedberg + Neuburg-Schrobenhausen](https://tonnenleerung.de), serving LK Aichach-Friedberg + Neuburg-Schrobenhausen, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: tonnenleerung_de
      args:
        url: URL
        
```

### Configuration Variables

**url**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: tonnenleerung_de
      args:
        url: nd-sob/neuburg-donau/abbevillestrasse/
        
```

should work with full ULR as well.

```yaml
waste_collection_schedule:
    sources:
    - name: tonnenleerung_de
      args:
        url: https://tonnenleerung.de/aic-fdb/affing
```

## How to get the source argument

Go to [https://tonnenleerung.de](https://tonnenleerung.de) and search your address. Use the url after https://tonnenleerung.de/ url parameter.

e.g https://tonnenleerung.de/nd-sob/neuburg-donau/abbevillestrasse/ -> nd-sob/neuburg-donau/abbevillestrasse/
