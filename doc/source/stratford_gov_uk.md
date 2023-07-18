# Stratford DC

Support for schedules provided by [Stratford-On-Avon District Council](https://stratford.gov.uk/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: stratford_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**  
*(string) (optional) (preferred method)*

This is required if you do not supply any other options. Using a UPRN removes the need to do an address look up using web requests.

## Example using UPRN

```yaml
waste_collection_schedule:
    sources:
    - name: stratford_gov_uk
      args:
        uprn: "10024633309"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

Otherwise you can use the Inspect tool after typing your address on Stratford-on-Avon's [When We Collect](https://www.stratford.gov.uk/waste-recycling/when-we-collect.cfm) page.

Simply search for your address with the Inspect tool set to view Network requests, look for the POST request and view its payload. You're looking for `frmUPRN=`.

