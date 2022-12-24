# Walsall Council

Support for schedules provided by [Walsall Council](https://cag.walsall.gov.uk/BinCollections/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: walsall_gov_uk
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
    - name: walsall_gov_uk
      args:
        uprn: "100071103746"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to [https://www.findmyaddress.co.uk/](https://www.findmyaddress.co.uk/) and entering in your address details.

Otherwise you can inspect the web requests on [Walsall Council](https://www.environmentfirst.co.uk/) having searched for and selected your address details. Your UPRN is the collection of digits at the end of the URL, for example: `https://cag.walsall.gov.uk/BinCollections/GetBins?uprn=100071103746`
