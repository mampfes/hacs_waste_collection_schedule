# Oxford City Council

Support for schedules provided by [Oxford City Council](https://www.oxford.gov.uk/), in the UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: oxford_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
        postcode: POSTCODE
```

### Configuration Variables

**uprn**<br>
*(string)*

The "Unique Property Reference Number" for your address. You can find it by searching for your address at https://www.findmyaddress.co.uk/.

**postcode**<br>
*(string)*

The Post Code for your address. This needs to match the postcode corresponding to your UPRN.

## Example
```yaml
waste_collection_schedule:
    sources:
    - name: oxford_gov_uk
      args:
        uprn: 100120827594
        postcode: OX4 1RB
```

## Returned Collectons
This source will return the next collection date for each container type.
If you don't subscribe to a brown garden waste bin, we don't return data for it.

## Returned collection types

### Green Rubbish Bin
Green Bin for general waste

### Blue Recycling Bin
Blue Bin for mixed recycling 

### Brown Garden Waste Bin
Brown Bin for garden waste.
If you don't pay for a garden waste bin, it won't be included.

### Food Waste Caddy
Green Caddy for food waste.
