# Swale Borough Council

Support for schedules provided by [Swale Borough Council](https://swale.gov.uk/), in the UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: swale_gov_uk
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
    - name: swale_gov_uk
      args:
        uprn: 100062375927
        postcode: ME10 3HT
```

## Returned Collections

This source will return the next collection date for each container type.

## Returned collection types

### Refuse

Green bin is for general waste.

### Recycling

Blue bin is for recycling.

### Garden

Garden Waste.

### Food

Food bin
