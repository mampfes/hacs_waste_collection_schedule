# Borough of Broxbourne Council

Support for schedules provided by [Borough of Broxbourne Council](https://www.broxbourne.gov.uk/), in the UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: broxbourne_gov_uk
      args:
        uprn: UNIQUE_PROPERTY_REFERENCE_NUMBER
        postcode: POSTCODE
```

### Configuration Variables

**uprn**  
*(string)*

The "Unique Property Reference Number" for your address. You can find it by searching for your address at <https://www.findmyaddress.co.uk/>.

**postcode**  
*(string)*

The Post Code for your address. This needs to match the postcode corresponding to your UPRN.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: broxbourne_gov_uk
      args:
        uprn: 148028240
        postcode: EN11 8PU
```

## Returned Collections

This source will return the next collection date for each container type serviced at your address.
If you don't subscribe to a garden waste bin, we don't return data for it.

## Returned collection types

### Domestic

Black bin for general waste

### Recycling

Black recycling box for mixed recycling

### Green Waste

Green Bin for garden waste.
If you don't pay for a garden waste bin, it won't be included.

### Food

Green or Brown Caddy for food waste.
