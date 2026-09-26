# Abfallwirtschaftsbetrieb Landkreis Ahrweiler

Support for schedules provided by [Abfallwirtschaftsbetrieb Landkreis Ahrweiler](https://www.meinawb.de).

Bin collection service from Kreis Ahrweiler/Germany

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: meinawb_de
      args:
        city: CITY
        street: STREET
        house_number: HOUSE_NUMBER
        address_suffix: ADDRESS_SUFFIX
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

**address_suffix**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: meinawb_de
      args:
        city: Oberzissen
        street: Lindenstrasse
        house_number: '1'
```
