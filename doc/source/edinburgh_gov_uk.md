# City of Edinburgh Council

Support for bin collection schedules provided by the [City of Edinburgh Council](https://www.edinburgh.gov.uk/homepage/10474/bin-collections).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: edinburgh_gov_uk
args:
  postcode: "EH10 4AY"
  paon: "1 Morningside Road"  # optional
```

## Configuration variables

**postcode**  
*(string) (required)* — The property's UK postcode.

**paon**  
*(string) (optional)* — The primary addressable object, such as the house number and street name. The street name must match the council directory record when supplied.

## How to find the street name

PAON means “Primary Addressable Object Name”. Use the house number and street name shown for the property by the council. For example, for `1 Morningside Road`, use `1 Morningside Road` as the `paon` value. The source searches the council's directory for the street and retrieves the collection calendar assigned to it.

If only a postcode is available, omit `paon`; the source attempts to resolve the street using postcode geocoding and OpenStreetMap reverse geocoding. Supplying `paon` is recommended because a postcode can cover more than one street.

## Returned waste types

The source returns collection dates for:

- Food Waste Bin
- Brown Garden Waste Bin
- Grey Bin
- Green Bin
- Glass Box
