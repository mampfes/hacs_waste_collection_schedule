# KWU Entsorgung Landkreis Oder-Spree

Support for schedules provided by [KWU Entsorgung Landkreis Oder-Spree](https://www.kwu-entsorgung.de/).

Source for KWU Entsorgung, Germany

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kwu_de
      args:
        city: CITY
        street: STREET
        number: NUMBER
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kwu_de
      args:
        city: Erkner
        street: "Heinrich-Heine-Stra\xDFe"
        number: '11'
```
