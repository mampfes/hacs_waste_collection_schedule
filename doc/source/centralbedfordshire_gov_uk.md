# Central Bedfordshire Council

Support for schedules provided by [Central Bedfordshire Council](https://www.centralbedfordshire.gov.uk/waste-and-recycling/waste-collection-schedule), serving Central Bedfordshire, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: centralbedfordshire_gov_uk
      args:
        postcode: POSTCODE
        house_name: HOUSE_NAME

```

### Configuration Variables

**POSTCODE**
*(string) (required)*

Your postcode, with or without a space (both `SG18 0LL` and `SG180LL` work).

**HOUSE_NAME**
*(string) (required)*

The start of your address exactly as it appears in the address dropdown on [Central Bedfordshire Council's website](https://www.centralbedfordshire.gov.uk/waste-and-recycling/waste-collection-schedule) after you search for your postcode. The dropdown lists entries in the form `1 Chestnut Avenue, Biggleswade, SG18 0LL`, so use just the leading house number and street (`1 Chestnut Avenue`).

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: centralbedfordshire_gov_uk
      args:
        postcode: "SG180LL"
        house_name: "1 Chestnut Avenue"
```
