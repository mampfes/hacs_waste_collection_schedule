# Northumberland County Council

Support for schedules provided by [Northumberland County Council](https://www.northumberland.gov.uk), serving Northumberland, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: northumberland_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
        postcode: POSTCODE
```

### Configuration Variables

**uprn**
*(string) (required)*

Your Unique Property Reference Number (UPRN).

**postcode**
*(string) (required)*

Your property postcode (e.g. `NE46 1UF`).

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: northumberland_gov_uk
      args:
        uprn: "100110637553"
        postcode: "NE46 1UF"
```

## How to find your UPRN and postcode

Visit <https://bincollection.northumberland.gov.uk/postcode>, enter your postcode, and select your address. The UPRN is shown in the address dropdown option value.

Alternatively, find your UPRN at <https://www.findmyaddress.co.uk/>.
