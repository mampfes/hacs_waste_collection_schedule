# Vale of Glamorgan Council

Support for schedules provided by [Vale of Glamorgan Council](https://valeofglamorgan.gov.uk/).

Source for Vale of Glamorgan Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: valeofglamorgan_gov_uk
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
    - name: valeofglamorgan_gov_uk
      args:
        uprn: 64003486
```
