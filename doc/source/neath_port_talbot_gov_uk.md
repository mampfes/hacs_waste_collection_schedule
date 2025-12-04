# Neath Port Talbot

Support for schedules provided by [Neath Port Talbot](https://www.npt.gov.uk/), serving Neath and Port Talbot, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: neath_port_talbot_gov_uk
      args:
        uprn: "UPRN"
        postcode: "POSTCODE"
```

### Configuration Variables

**uprn**  
*(String | Integer) (required)*

**postcode**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: neath_port_talbot_gov_uk
      args:
        uprn: "100100599841"
        postcode: "SA11 3HY"
```

## How to get the source argument

Find your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
