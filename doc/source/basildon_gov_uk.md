# Basildon Council

Support for schedules provided by [Basildon Council](https://www3.basildon.gov.uk/website2/postcodes.nsf/frmMyBasildon), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: basildon_gov_uk
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
    - name: basildon_gov_uk
      args:
        uprn: "100090277795"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.
