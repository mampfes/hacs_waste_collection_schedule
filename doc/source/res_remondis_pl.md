# REMONDIS (res.remondis.pl)

Support for schedules provided by [REMONDIS (res.remondis.pl)](https://res.remondis.pl/harmonogram/).

Source for REMONDIS waste collection schedules (e.g. Sosnowiec).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: res_remondis_pl
      args:
        city: CITY
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: res_remondis_pl
      args:
        city: Sosnowiec
        street: Malinowa
        house_number: '6'
```
