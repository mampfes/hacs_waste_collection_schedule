# London Borough of Barking and Dagenham

Support for schedules provided by [London Borough of Barking and Dagenham](https://www.lbbd.gov.uk/), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: lbbd_gov_uk
      args:
        uprn: UPRN_CODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: lbbd_gov_uk
      args:
        uprn: "100014033"
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.