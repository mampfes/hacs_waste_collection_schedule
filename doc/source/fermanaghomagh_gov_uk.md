# Fermanagh and Omagh District Council

Support for schedules provided by [Fermanagh and Omagh District Council](https://www.fermanaghomagh.com/).

Source for the Fermanagh and Omagh District Council, Northern Ireland

## Configuration via configuration.yaml

### Using property_id

```yaml
waste_collection_schedule:
  sources:
    - name: fermanaghomagh_gov_uk
      args:
        property_id: PROPERTY_ID
```

### Using postcode and house_number

```yaml
waste_collection_schedule:
  sources:
    - name: fermanaghomagh_gov_uk
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
    - name: fermanaghomagh_gov_uk
      args:
        property_id: GMtpf6Tk1glK57Zj
```

### Using postcode and house_number

```yaml
waste_collection_schedule:
  sources:
    - name: fermanaghomagh_gov_uk
      args:
        postcode: BT78 1RG
        house_number: '1'
```

## How to get the source arguments

Provide your postcode and house number (or name), or the property ID as found in the URL when looking up your bin collection days.
