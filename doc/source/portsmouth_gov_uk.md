# Portsmouth City Council

Support for schedules provided by [Portsmouth City Council](https://www.portsmouth.gov.uk).

Source for waste collection services for Portsmouth City Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: portsmouth_gov_uk
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
    - name: portsmouth_gov_uk
      args:
        uprn: 1775027540
```
