# East Devon District Council

Support for schedules provided by [East Devon District Council](https://eastdevon.gov.uk/), serving East Devon, UK.

Data is retrieved from East Devon's Cloud9 citizen mobile API (same backend as the official East Devon app).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: eastdevon_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
```

or

```yaml
waste_collection_schedule:
    sources:
    - name: eastdevon_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
```

### Configuration Variables

**uprn**
*(string) (optional)*

**postcode**
*(string) (optional)*

**address**
*(string) (optional)*

Provide either `uprn`, or `postcode` together with `address`.

## Examples

Using a UPRN:

```yaml
waste_collection_schedule:
    sources:
    - name: eastdevon_gov_uk
      args:
        uprn: "010000246114"
```

Using a postcode and address:

```yaml
waste_collection_schedule:
    sources:
    - name: eastdevon_gov_uk
      args:
        postcode: "EX8 2AN"
        address: "1 Dagmar Road"
```

If the address does not uniquely identify a property, the integration reports
the matching addresses so you can copy an exact one.

## How to find your UPRN

An easy way to discover your Unique Property Reference Number (UPRN) is by looking at the url of your collection schedule on the East Devon District Council website. The set of numbers at the end of the url are your uprn.

For example: 
eastdevon.gov.uk/recycling-and-waste/recycling-and-waste-information/when-is-my-bin-collected/?UPRN=`010000246114`_

Alternatively, you can go to [Find My Address](https://www.findmyaddress.co.uk/) and search for
your address.
