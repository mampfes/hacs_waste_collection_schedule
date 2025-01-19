# Bolton Council

Support for schedules provided by [Bolton Council](https://carehomes.bolton.gov.uk/bins.aspx), serving Bolton, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: bolton_gov_uk
      args:
        postcode: POSTCODE
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**postcode**
*(string) (required)*

Your postcode, with or without a space (e.g., "BL1 5XR" or "BL15XR").

**house_number**
*(string) (required)*

Your house number. This should match the start of your address exactly as it appears on the [Bolton Council](https://www.bolton.gov.uk/next-bin-collection) website. Named properties should be entered as the house number.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: bolton_gov_uk
      args:
        postcode: "BL2 2QB"
        house_number: "14"
```

## Collection Types

This source returns the following types of collections:

**Grey Bin**
General waste

**Beige Bin**
Paper and card

**Burgundy Bin**
Glass, cans, and plastic bottles

**Green Bin**
Food and garden waste

**Food Container**
Food waste
