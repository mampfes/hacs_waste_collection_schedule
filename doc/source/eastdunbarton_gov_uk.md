# East Dunbartonshire Council

Support for schedules provided by [East Dunbartonshire Council](https://eastdunbarton.gov.uk).

Source for East Dunbartonshire Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eastdunbarton_gov_uk
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
    - name: eastdunbarton_gov_uk
      args:
        uprn: '132020996'
```
