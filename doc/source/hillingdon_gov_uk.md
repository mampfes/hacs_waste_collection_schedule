# London Borough of Hillingdon

Support for waste collection schedules provided by [London Borough of Hillingdon](https://www.hillingdon.gov.uk), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hillingdon_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**
*(string) (required)*

Your Unique Property Reference Number (UPRN).

## How to find your `uprn`

An easy way to discover your UPRN is by going to [FindMyAddress](https://www.findmyaddress.co.uk/) and entering your address details.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hillingdon_gov_uk
      args:
        uprn: "100021484628"
```

## Bin types returned

| Provider description | Returned type | Icon |
|---------------------|--------------|------|
| Dry mixed recycling | Dry mixed recycling | `Icons.RECYCLING` |
| Household waste | Household waste | `Icons.GENERAL_WASTE` |
| Garden waste | Garden waste | `Icons.GARDEN` |
| Food waste | Food waste | `Icons.BIO_KITCHEN` |
| Trade Sacks General Waste | Trade Sacks General Waste | `Icons.COMMERCIAL` |
