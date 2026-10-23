# HVC Groep

Support for schedules provided by [HVC Groep](https://www.hvcgroep.nl).

Source for the Dutch HVCGroep waste management.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hvcgroep_nl
      args:
        postal_code: POSTAL_CODE
        house_number: HOUSE_NUMBER
        house_letter: HOUSE_LETTER
        suffix: SUFFIX
        service: SERVICE
```

### Configuration Variables

**postal_code**  
*(string) (required)*

**house_number**  
*(string) (required)*

**house_letter**  
*(string) (optional)*

**suffix**  
*(string) (optional)*

**service**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hvcgroep_nl
      args:
        postal_code: 2404EN
        house_number: '7'
        service: alphenaandenrijn
```
