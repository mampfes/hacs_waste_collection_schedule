# Trafford Council

Support for schedules provided by [Trafford Council](https://www.trafford.gov.uk/BinCollections/).

Waste collection schedules for Trafford Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: trafford_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
        garden_waste: GARDEN_WASTE
```

### Configuration Variables

**postcode**  
*(string) (required)*

**address**  
*(string) (required)*

**garden_waste**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: trafford_gov_uk
      args:
        postcode: M41 5BG
        address: 130A Flixton Road, Urmston, Trafford, Manchester, M41 5BG
```

## How to get the source arguments

Enter the postcode and the full address returned by Trafford Council. Submit part of the address once to receive matching suggestions. Enable garden waste only if the green bin displays a valid paid permit; food waste is collected from green bins without a permit.
