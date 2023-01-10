# KWU Entsorgung

Support for schedules provided by [kwu-entsorgung.de](https://www.kwu-entsorgung.de/) located Landkreis Oder-Spree, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kwu_de
      args:
        city: Bad Saarow
        street: Ahornallee
        number: 1
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**number**  
*(string) (required)*

## How to get the source arguments

Visit [Entsorgungskalender](https://www.kwu-entsorgung.de/?page_id=337`) and search for your address. The `city`, `street` and `number` argument should exactly match the autocomplete result.
