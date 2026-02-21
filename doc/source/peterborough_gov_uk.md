# Peterborough City Council

Support for schedules provided by [Peterborough City Council](https://www.peterborough.gov.uk/residents/rubbish-and-recycling/bins).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: peterborough_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
        post_code: POST_CODE
```

### Configuration Variables

**uprn**
*(string) (required)*

This is your Unique Property Reference Number (UPRN)

**post_code**  
*(string) (required)*

This is required if you do not supply a UPRN. Single space between 1st and 2nd part of postcode is optional.

#### How to find your `UPRN`

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
Otherwise you can use the [Peterborough Council website](https://report.peterborough.gov.uk/waste) and enter in your postcode and select your address, the web page you will be taken to will be in the format of `https://report.peterborough.gov.uk/waste/{postcode}:{uprn}`.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: peterborough_gov_uk
      args:
        uprn: 100090214774
        post_code: PE57AX
```
