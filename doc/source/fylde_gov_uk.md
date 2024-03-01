# Fylde Council

Support for schedules provided by [Fylde Council](https://fylde.gov.uk/resident/), serving the Borough of Fylde, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: fylde_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: fylde_gov_uk
      args:
        uprn: "100010402452"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.
