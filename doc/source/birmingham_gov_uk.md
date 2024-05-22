# Birmingham City Council

Support for schedules provided by [Birmingham City Council](https://www.birmingham.gov.uk/), in the UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: birmingham_gov_uk
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
    - name: birmingham_gov_uk
      args:
        uprn: 100070321799
        postcode: B27 6TF
```

## Returned Collections
This source will return the next collection date for each container type.

## Returned collection types

### Household Collection
Grey lid rubbish bin is for general waste.

### Recycling Collection
Green lid recycling bin is for dry recycling (metals, glass and plastics).
Blue lid recycling bin is for paper and card.

### Green Recycling Chargeable Collections
Green Recycling (Chargeable Collections).
