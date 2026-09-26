# London Borough of Barking and Dagenham

Support for schedules provided by [London Borough of Barking and Dagenham](https://www.lbbd.gov.uk/).

Source for London Borough of Barking and Dagenham.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lbbd_gov_uk
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
    - name: lbbd_gov_uk
      args:
        uprn: '100014033'
```
