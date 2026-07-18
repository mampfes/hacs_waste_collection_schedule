# Merri-bek City Council

Support for schedules provided by [Merri-bek City Council](https://www.merri-bek.vic.gov.au).

Source for Merri-bek City Council (VIC) rubbish collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: merri_bek_vic_gov_au
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
    - name: merri_bek_vic_gov_au
      args:
        address: 1 Vincent Street Oak Park 3046
```
