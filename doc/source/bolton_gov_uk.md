# Bolton Council

Support for schedules provided by [Bolton Council](https://www.bolton.gov.uk/), in the UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: bolton_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)*

Your postcode.

**uprn**  
*(string) (required)*

The "Unique Property Reference Number" for your address.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: bolton_gov_uk
      args:
        postcode: "BL2 2QB"
        uprn: "100010940555"
```

## Returned Collections

This source will return the next collection dates for each bin type:

### Grey bin
General waste

### Beige bin
Paper and card

### Burgundy bin
Glass, cans, and plastic bottles

### Green bin
Food and garden waste

### Food container
Food waste 