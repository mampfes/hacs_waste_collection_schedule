# Neath Port Talbot Council

Support for schedules provided by [Neath Port Talbot Council](https://www.npt.gov.uk/).

Source for waste collection services for Neath Port Talbot Council

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: neath_port_talbot_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)*

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: neath_port_talbot_gov_uk
      args:
        postcode: SA11 3HW
        uprn: 100100601042
```

## How to get the source arguments

An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details, or by searching for your address at https://uprn.uk/. The council's site asks for the postcode before the property, so both are needed. Collection dates are only given for the next two weeks.
