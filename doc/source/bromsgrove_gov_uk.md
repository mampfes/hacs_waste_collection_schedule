# Bromsgrove District Council

Support for schedules provided by [Bromsgrove District Council](https://www.bromsgrove.gov.uk/), in the UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: bromsgrove_gov_uk
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
    - name: bromsgrove_gov_uk
      args:
        uprn: 10094552413
        postcode: B61 8DA
```

## Returned Collections
This source will return the next collection date for each container type.

## Returned collection types

### Household Collection
Grey bin is for general waste.

### Recycling Collection
Green bin is for dry recycling (metals, glass, plastics, paper and card).

### Garden waste Chargeable Collections
Brown bin if for gareden waste. This is a annual chargable service.
