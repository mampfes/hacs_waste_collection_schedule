# Powys County Council

Support for schedules provided by [Powys County Council](https://en.powys.gov.uk/binday).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: powys_gov_uk
      args:
        postcode: POSTCODE
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**postcode**
*(string) (required)*

Your property postcode, e.g. `SY16 2PQ`.

**uprn**
*(string) (required)*

Your Unique Property Reference Number (UPRN).

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: powys_gov_uk
      args:
        postcode: "SY16 2PQ"
        uprn: "100100307820"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.
