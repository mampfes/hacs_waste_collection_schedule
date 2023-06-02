# East Riding of Yorkshire Council

Support for schedules provided by [East Riding of Yorkshire Council](https://eastriding.gov.uk), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: eastriding_gov_uk
      args:
        postcode: POSTCODE
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**postcode**</br>
*(string) (required)*

**uprn**</br>
*(string) (required)*


## Example
```yaml
waste_collection_schedule:
    sources:
    - name: eastriding_gov_uk
      args:
        postcode: "DN14 6BJ"
        uprn: "010002364380"
```

#### How to find your `UPRN`
You can discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.



