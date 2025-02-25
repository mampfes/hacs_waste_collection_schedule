# Amber Valley Borough Council

Support for schedules provided by [Amber Valley Borough Council](https://www.ambervalley.gov.uk/rubbish-waste-and-recycling/bin-collection-dates/), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: ambervalley_gov_uk
      args:
        uprn: UPRN_CODE
        predict: PREDICT (optional) True or False
```

### Configuration Variables

**uprn**  
*(string) (required)*

**predict**  
*(boolean) (optional|defaults to false)*

If `predict` is set to `True`, the source will try to predict the next collection date based on the previous collection dates and collection frequency. By default this source only provides the next collection date.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: ambervalley_gov_uk
      args:
        uprn: "100030011612"
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
