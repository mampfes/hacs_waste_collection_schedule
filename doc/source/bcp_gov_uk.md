# BCP Council

Support for schedules provided by [BCP Council](https://www.bcpcouncil.gov.uk/), serving Bournemouth, Christchurch and Poole UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: bcp_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables

**uprn**<br>
*(string) (required)*


## Example using UPRN
```yaml
waste_collection_schedule:
    sources:
    - name: bcp_gov_uk
      args:
        uprn: "10013448804"
```


#### How to get the source argument
An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.



