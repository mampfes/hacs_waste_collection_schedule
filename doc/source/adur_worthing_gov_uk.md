# Adur & Worthing Councils

Support for schedules provided by [Adur & Worthing Councils](https://www.adur-worthing.gov.uk/bin-day/), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: adur_worthing_gov_uk
      args:
        postcode: POSTCODE
        address: FIRST LINE OF ADDRESS (X, STREET NAME)
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (optional)*

**address**  
*(string) (optional)*

**uprn**  
*(string) (optional)*

Supply both `postcode` and `address` args, or just the `uprn` arg

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: adur_worthing_gov_uk
      args:
        postcode: BN15 9UX
        address: 1 Western Road
```
```yaml
waste_collection_schedule:
    sources:
    - name: adur_worthing_gov_uk
      args:
        uprn: 100062209109
        
```

## How to get the uprn argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.