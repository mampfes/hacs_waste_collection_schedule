# Hastings Borough Council

Support for schedules provided by [Hastings Borough Council](https://www.hastings.gov.uk/waste_recycling/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: hastings_gov_uk
      args:
        postcode: POSTCODE
        house_humber: HOUSE_NUMBER
        uprn: UPRN
```

### Configuration Variables

**postcode**
*(string) (required)*

**house_number**
*(string) (required)*

**uprn**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: hastings_gov_uk
      args:
        postcode: "TN34 2DL"
        house_number: "28A"
        uprn: "10070609836"
```

## How to get the source argument

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.