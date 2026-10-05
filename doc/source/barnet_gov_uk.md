# London Borough of Barnet

Support for schedules provided by [London Borough of Barnet](https://www.barnet.gov.uk/).

Source script for barnet.gov.uk

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: barnet_gov_uk
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
    - name: barnet_gov_uk
      args:
        uprn: '200062903'
```
