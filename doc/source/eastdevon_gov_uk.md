# East Devon District Council

Support for schedules provided by [East Devon District Council](https://eastdevon.gov.uk/), serving East Devon, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: eastdevon_gov_uk
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
    - name: eastdevon_gov_uk
      args:
        uprn: "010000246114"
```

## How to find your UPRN

An easy way to discover your Unique Property Reference Number (UPRN) is by looking at the url of you collection schedule on the East Devon District Council website. The set of numbers at the end of the url are your uprn.

For example: 
eastdevon.gov.uk/recycling-and-waste/recycling-and-waste-information/when-is-my-bin-collected/?UPRN=`010000246114`_

Alternatively, you can go to  to [Find My Address](https://www.findmyaddress.co.uk/) and search for
your address.
