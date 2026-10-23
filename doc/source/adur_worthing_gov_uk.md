# Adur & Worthing Councils

Support for schedules provided by [Adur & Worthing Councils](https://adur-worthing.gov.uk).

Source for adur-worthing.gov.uk services for Adur & Worthing, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: adur_worthing_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (optional)*

**address**  
*(string) (optional)*

**uprn**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: adur_worthing_gov_uk
      args:
        postcode: BN15 9UX
        address: 1 Western Road North
```

## How to get the source arguments

An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details
