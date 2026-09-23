# Wirral Council

Support for schedules provided by [Wirral Council](https://wirral.gov.uk/), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wirral_gov_uk
      args:
        address_value: ADDRESS_VALUE
```

### Configuration Variables

**address_value**  
*(string) (required)*

The address (UPRN) value for your property. To find it, go to https://www.wirral.gov.uk/bins-and-recycling/bin-collection-dates, enter your postcode and select your address. The number at the end of the resulting web address (for example `https://www.wirral.gov.uk/bins-and-recycling/bin-collection-dates/view/42119794`) is your address value. The older 12-digit zero-padded values (e.g. `000042119794`) are still accepted.

**postcode**  
*(string) (optional)*

Your postcode, e.g. `CH49 4NP`. No longer needed, but still accepted so existing configurations keep working.

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: wirral_gov_uk
      args:
        address_value: "42119794"
```

```yaml
waste_collection_schedule:
  sources:
    - name: wirral_gov_uk
      args:
        postcode: "CH49 4NP"
        address_value: "000042037487"
```
