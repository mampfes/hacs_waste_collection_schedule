# New Forest District Council

Support for schedules provided by [New Forest District Council](https://www.newforest.gov.uk/findyourcollection).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: newforest_gov_uk
      args:
        postcode: POSTCODE
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**postcode**
*(string) (required)*

Your property's postcode, e.g. `SO40 8XX`.

**uprn**
*(string) (required)*

Your Unique Property Reference Number (UPRN).

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: newforest_gov_uk
      args:
        postcode: "SO40 8XX"
        uprn: "100060514912"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.
