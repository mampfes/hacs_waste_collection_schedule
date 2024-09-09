# Islington Council

Support for schedules provided by [Islington Council](https://www.islington.gov.uk/), serving Islington, London, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: islington_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**<br>
*(string) (required)*


## Example using UPRN

```yaml
waste_collection_schedule:
    sources:
    - name: islington_gov_uk
      args:
        uprn: "10001295652"
```

#### How to find your `UPRN`

Select your address on <https://www.islington.gov.uk/your-area>. You get redirected to your collection overview. The URL contains your UPRN (`https://www.islington.gov.uk/your-area?Postcode=unused&Uprn={UPRN}`)

Alternatively, you can discover what your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.
