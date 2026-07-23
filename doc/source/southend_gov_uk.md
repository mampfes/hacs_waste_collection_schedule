# Southend-on-Sea City Council

Support for schedules provided by [Southend-on-Sea City Council](https://www.southend.gov.uk), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: southend_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**
*(string) (required)*

**postcode**
*(string) (optional) (legacy, use UPRN instead)*

**address**
*(string) (optional) (legacy, use UPRN instead)*

## Example using UPRN

```yaml
waste_collection_schedule:
    sources:
    - name: southend_gov_uk
      args:
        uprn: "100090691871"
```

## Example using postcode and address (legacy)

```yaml
waste_collection_schedule:
    sources:
    - name: southend_gov_uk
      args:
        postcode: "SS3 9JD"
        address: "38 Thorpedene Gardens, Shoeburyness"
```

#### How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.
