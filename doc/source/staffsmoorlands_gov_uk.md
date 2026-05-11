# Staffordshire Moorlands District Council

Support for schedules provided by [Staffordshire Moorlands District Council](https://www.staffsmoorlands.gov.uk/article/6911/Find-your-bin-day), serving the Staffordshire Moorlands district, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: staffsmoorlands_gov_uk
      args:
        postcode: POSTCODE
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**postcode**
*(string) (required)*

Your property postcode, e.g. `ST8 7EA`.

**uprn**
*(string) (required)*

Your Unique Property Reference Number (UPRN).

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: staffsmoorlands_gov_uk
      args:
        postcode: "ST8 7EA"
        uprn: "10010602737"
```

## How to find your `UPRN`

Visit <https://www.staffsmoorlands.gov.uk/findyourbinday>, enter your postcode and look at the address dropdown — the value associated with your address is your UPRN.

Alternatively, use <https://www.findmyaddress.co.uk/> and enter your address details.
