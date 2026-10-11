# Lisburn and Castlereagh City Council

Support for schedules provided by [Lisburn and Castlereagh City Council](https://lisburncastlereagh.gov.uk/).

Source for the Lisburn and Castlereagh City Council

## Configuration via configuration.yaml

### Using property_id

```yaml
waste_collection_schedule:
  sources:
    - name: lisburn_castlereagh_gov_uk
      args:
        property_id: PROPERTY_ID
```

### Using postcode and house_number

```yaml
waste_collection_schedule:
  sources:
    - name: lisburn_castlereagh_gov_uk
      args:
        postcode: POSTCODE
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**property_id**  
*(string) (alternative)*

**postcode**  
*(string) (alternative)*

**house_number**  
*(string) (alternative)*

Provide one of: `property_id` or `postcode` + `house_number`.

## Example

### Using property_id

```yaml
waste_collection_schedule:
  sources:
    - name: lisburn_castlereagh_gov_uk
      args:
        property_id: RTTKBJY77wmTr5wP
```

### Using postcode and house_number

```yaml
waste_collection_schedule:
  sources:
    - name: lisburn_castlereagh_gov_uk
      args:
        postcode: BT28 1AG
        house_number: 19A
```

## How to get the source arguments

Provide your postcode and house number (or name), or the property ID as found in the URL when looking up your bin collection days.
