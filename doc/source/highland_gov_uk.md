# Highland

Support for schedules provided by [Highland](https://www.highland.gov.uk/).

Source for Highland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: highland_gov_uk
      args:
        uprn: UPRN
        predict: PREDICT
```

### Configuration Variables

**uprn**  
*(string) (required)*

**predict**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: highland_gov_uk
      args:
        uprn: 130108578
        predict: 'true'
```
