# Forest of Dean District Council

Support for waste collection schedules provided by [Forest of Dean District Council](https://www.fdean.gov.uk/), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: forest_of_dean_gov_uk
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

The full address string exactly as returned by the address lookup on the waste collection enquiry page.

## How to find your `address`

1. Go to the [Forest of Dean waste collection enquiry page](https://community.fdean.gov.uk/s/waste-collection-enquiry).
2. Start typing your postcode into the address lookup field.
3. Select your property from the autocomplete suggestions.
4. Use the full address string exactly as it appears in the suggestion (including the postcode), for example `8 SOUTHFIELD ROAD, COLEFORD, GL16 8BZ`.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: forest_of_dean_gov_uk
      args:
        address: "8 SOUTHFIELD ROAD, COLEFORD, GL16 8BZ"
```

## Bin types returned

| Provider description | Returned type        | Icon                  |
|----------------------|----------------------|-----------------------|
| Garden Bin           | Garden Bin           | `Icons.ORGANIC`       |
| Green Recycling Box  | Green Recycling Box  | `Icons.RECYCLING`     |
| Outdoor Food Caddy   | Outdoor Food Caddy   | `Icons.BIO_KITCHEN`   |
| Blue Bag             | Blue Bag             | `Icons.RECYCLING`     |
| 240 Litre Refuse     | 240 Litre Refuse     | `Icons.GENERAL_WASTE` |
