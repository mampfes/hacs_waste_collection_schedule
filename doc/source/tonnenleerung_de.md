# tonnenleerung.de LK Aichach-Friedberg + Neuburg-Schrobenhausen

Support for schedules provided by [tonnenleerung.de LK Aichach-Friedberg + Neuburg-Schrobenhausen](https://tonnenleerung.de).

Source for tonnenleerung.de LK Aichach-Friedberg + Neuburg-Schrobenhausen.

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
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: tonnenleerung_de
      args:
        url: nd-sob/neuburg-donau/adalbert-stifter-strasse/
```

## How to get the source arguments

Open your street (or village) on https://tonnenleerung.de and copy the address of the page, e.g. `https://tonnenleerung.de/aic-fdb/affing`. The part after the domain (`aic-fdb/affing`) also works.
