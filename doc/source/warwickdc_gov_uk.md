# Warwick District Council

Support for schedules provided by [Warwick District Council](https://www.warwickdc.gov.uk/info/20465/rubbish_waste_and_recycling).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: warwickdc_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**  
*(string) (required)*


## Example using UPRN

```yaml
waste_collection_schedule:
    sources:
    - name: warwickdc_gov_uk
      args:
        uprn: "100070263501"
```

## How to find your `UPRN`

An easy way to find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

Alternatively you can inspect the URL on [Warwick District Council](https://www.warwickdc.gov.uk/info/20465/rubbish_waste_and_recycling). Having searched for your collection schedule, your UPRN is the collection of digits at the end of the URL, for example: _https://estates7.warwickdc.gov.uk/PropertyPortal/Property/Recycling/`100070260258`_
