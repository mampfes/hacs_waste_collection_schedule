# Sheffield City Council

Support for schedules provided by [Sheffield City Council](https://wasteservices.sheffield.gov.uk/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: sheffield_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**<br>
*(string) (optional) (preferred method)*

This is required if you do not supply any other options. Using a UPRN removes the need to do an address look up using web requests.

## Example using UPRN
```yaml
waste_collection_schedule:
    sources:
    - name: sheffield_gov_uk
      args:
        uprn: "100050938234"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.

Otherwise you can inspect the URL on [Sheffield City Council's Waste Services](https://wasteservices.sheffield.gov.uk/) site having searched for and selected your address details. Your UPRN is the collection of digits at the end of the URL (before /calendar), for example: *https://wasteservices.sheffield.gov.uk/property/`100050938234`* or *https://wasteservices.sheffield.gov.uk/property/`100050938234`/calendar*