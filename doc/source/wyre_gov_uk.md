# Wyre Council

Support for schedules provided by [Wyre Council](https://wyre.gov.uk/), serving Lichfield, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: wyre_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example using UPRN

```yaml
waste_collection_schedule:
    sources:
    - name: wyre_gov_uk
      args:
        uprn: "10094000847"
```

## How to find your `UPRN`

Your uprn is the collection of numbers at the end of the url when viewing your collection schedule on the Wyre Council web site.

Alternatively, you can discover what your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
