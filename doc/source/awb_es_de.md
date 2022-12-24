# AWB Esslingen

Support for schedules provided by [awb-es.de](https://www.awb-es.de) located in Baden Württemberg, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: awb_es_de
      args:
        city: Aichwald
        street: Alte Dorfstrasse
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

## How to get the source arguments

Visit (Abfuhrtermine)[`https://www.awb-es.de/abfuhr/abfuhrtermine/__Abfuhrtermine.html`] and search for your address. The `city` and `street` argument should exactly match the autocomplete result.
