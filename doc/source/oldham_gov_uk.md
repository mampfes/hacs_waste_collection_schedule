# Oldham Council

Support for schedules provided by [Oldham Council](https://www.oldham.gov.uk/), in the UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: oldham_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**<br>
*(string)*

The "Unique Property Reference Number" for your address. You can find it by searching for your address at https://www.findmyaddress.co.uk/.


## Example
```yaml
waste_collection_schedule:
    sources:
    - name: oldham_gov_uk
      args:
        uprn: "422000129104"
```

