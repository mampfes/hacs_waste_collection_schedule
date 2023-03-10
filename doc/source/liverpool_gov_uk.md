# Liverpool City Council

Support for schedules provided by [Liverpool City Council](http://liverpool.gov.uk/), serving Liverpool, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: liverpool_gov_uk
      args:
        uprn: UPRN
```

### Configuration Variables

**uprn**  
*(string) (required)*

This is required to unambiguously identify the property.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: liverpool_gov_uk
      args:
        uprn: "312345"

```

## How to find your `uprn`

You can find your house reference number by going to https://www.findmyaddress.co.uk/search and searching for your property.

You can also check the Liverpool City Council website by browsing to https://liverpool.gov.uk/Address/GetAddressesByPostcode/?postcode=L19 8LR and replacing postcode with your own. (You can leave a space in the URL or use %20 instead of the space)

## Returned collectons
The API will return the next collection dates for each container type. This will typically be the collections for the next 3 weeks but may vary over holiday periods

## Returned collection types

### Green
Green garden recycling

### Refuse
Purple non-recycling

### Recycling
Blue recycling bin/bag

