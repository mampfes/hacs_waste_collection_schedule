# Belmont City Council

Support for schedules provided by [Belmont City Council](https://www.belmont.wa.gov.au/).

Source for Belmont City Council rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: belmont_wa_gov_au
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
    - name: belmont_wa_gov_au
      args:
        address: 196 Abernethy Road Belmont 6104
```
