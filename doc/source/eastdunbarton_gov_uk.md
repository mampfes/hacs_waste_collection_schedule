# East Dunbartonshire Council

Support for schedules provided by [East Dunbartonshire Council](https://www.eastdunbarton.gov.uk/services/a-z-of-services/bins-waste-and-recycling/bins-and-recycling/), serving East Dunbartonshire, Scotland, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: eastdunbarton_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**
*(string) (required)*


## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: eastdunbarton_gov_uk
      args:
        uprn: "132020996"
```

## How to find your UPRN

An easy way to discover your Unique Property Reference Number (UPRN) is by looking at the url of you collection schedule on the East Dunbartonshire  Council website. The set of numbers at the end of the url are your uprn.

For example: 
eastdunbarton.gov.uk/services/a-z-of-services/bins-waste-and-recycling/bins-and-recycling/collections/?uprn=`132020996`


Alternatively, you can go to  to [Find My Address](https://www.findmyaddress.co.uk/) and search for
your address.



