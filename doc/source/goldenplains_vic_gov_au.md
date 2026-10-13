# Golden Plains Shire Council

Support for schedules provided by [Golden Plains Shire Council](https://www.goldenplains.vic.gov.au).

Source for Golden Plains Shire Council, VIC, AU

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: goldenplains_vic_gov_au
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
    - name: goldenplains_vic_gov_au
      args:
        address: 2 POPE STREET BANNOCKBURN 3331
```
