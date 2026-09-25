# Exeter City Council

Support for schedules provided by [Exeter City Council](https://exeter.gov.uk/), serving Exeter City, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: exeter_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**
*(string) (required)*

The Unique Property Reference Number (UPRN) of your property.

## Examples

```yaml
waste_collection_schedule:
    sources:
    - name: exeter_gov_uk
      args:
        uprn: "10013049539"
```

## How to find your UPRN

An easy way to discover your Unique Property Reference Number (UPRN) is by looking at the URL of your collection schedule on the Exeter City Council website. The set of numbers at the end of the URL is your UPRN.

For example:
_exeter.gov.uk/bins-and-recycling/bin-collections/when-is-my-bin-collected/?UPRN=`10013049539`_

Alternatively, you can go to [Find My Address](https://www.findmyaddress.co.uk/) and search for your address.
