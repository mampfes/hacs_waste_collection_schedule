# Shire of Serpentine Jarrahdale

Support for schedules provided by [Shire of Serpentine Jarrahdale](https://www.sjshire.wa.gov.au).

Source for www.sjshire.wa.gov.au Waste Collection Services

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sjshire_wa_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sjshire_wa_gov_au
      args:
        address: 5 Pingaring Court BYFORD WA 6122
```
