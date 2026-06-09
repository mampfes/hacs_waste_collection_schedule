# Baltimore County

Support for schedules provided by [Baltimore County](https://www.baltimorecountymd.gov/departments/public-works/solid-waste/collection-schedule), Maryland, USA.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: baltimore_county_md_us
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(string) (optional)*

Street address selected from the county suggestions, for example: 610 Gifford Ln, Monkton, MD 21111

## How to find your arguments

1. Open the Baltimore County collection schedule page.
2. Enter house number and street name in the Address field.
3. Select your full address from the dropdown suggestions.
4. Click Find.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: baltimore_county_md_us
      args:
        address: "610 Gifford Ln"
```

## Bin types returned

| Provider description | Returned type | Icon |
|---------------------|--------------|------|
| Trash | Trash | Icons.GENERAL_WASTE |
| Recycling | Recycling | Icons.RECYCLING |
| Yard Materials | Yard Materials | Icons.GARDEN |
| Bulk Pickup | Bulk Pickup | Icons.BULKY |
