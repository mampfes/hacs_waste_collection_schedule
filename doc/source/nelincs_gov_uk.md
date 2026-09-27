# North East Lincolnshire Council

Support for schedules provided by [North East Lincolnshire Council](https://www.nelincs.gov.uk/).

Source for North East Lincolnshire Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nelincs_gov_uk
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
    - name: nelincs_gov_uk
      args:
        uprn: 11042949
```
