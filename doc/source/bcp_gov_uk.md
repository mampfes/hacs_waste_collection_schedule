# BCP Council

Support for schedules provided by [BCP Council](https://bcpportal.bcpcouncil.gov.uk).

Bin collection data for Bournemouth, Christchurch and Poole Council, UK

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bcp_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bcp_gov_uk
      args:
        uprn: 10013449141
```
