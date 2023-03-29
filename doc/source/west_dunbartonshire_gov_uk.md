# West Dunbartonshire Council

Support for schedules provided by [West Dunbartonshire Council](https://www.west-dunbarton.gov.uk), serving West Dunbartonshire district in Scotland, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: west_dunbartonshire_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**<br>
*(string) (required)*


#### How to find your `UPRN`
An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.
Otherwise you can inspect the web address on the West Dunbartonshire Council website, after entering your details, the UPRN will be found in the url. Eg `https://www.west-dunbarton.gov.uk/recycling-and-waste/bin-collection-day/?uprn=129003614` is a UPRN of `129003614`.

## Example
```yaml
waste_collection_schedule:
    sources:
    - name: west_dunbartonshire_gov_uk
      args:
        uprn: 129003614
```
