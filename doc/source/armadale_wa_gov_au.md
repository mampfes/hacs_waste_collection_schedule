# Armadale (Western Australia)

Support for schedules provided by [Armadale (Western Australia)](https://my.armadale.wa.gov.au).

Source for Armadale (Western Australia).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: armadale_wa_gov_au
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
    - name: armadale_wa_gov_au
      args:
        address: 23 Sexty St, ARMADALE
```
