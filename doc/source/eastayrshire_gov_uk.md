# East Ayrshire Council

Support for schedules provided by [East Ayrshire Council](https://www.east-ayrshire.gov.uk/Housing/RubbishAndRecycling/Collection-days/ViewYourRecyclingCalendar.aspx).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: eastayrshire_gov_uk
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
    - name: eastayrshire_gov_uk
      args:
        uprn: "127072649"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering your address details.