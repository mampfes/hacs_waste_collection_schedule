# Wirral Council

Support for schedules provided by [Wirral Council](https://wirral.gov.uk/), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wirral_gov_uk
      args:
        address_value: ADDRESS_VALUE
        postcode: POSTCODE # optional, no longer used
```

### Configuration Variables

**address_value**  
*(string) (required)*

The number that identifies your address on the Wirral bin collection dates page. To find it, go to https://www.wirral.gov.uk/bins-and-recycling/bin-collection-dates, enter your postcode and select your address. The number at the end of the resulting web address (for example `.../view/42037487`) is your address value.

The 12-digit, zero-padded value used by the old Wirral bin calendar (for example `000042037487`) still works: the leading zeros are removed.

**postcode**  
*(string) (optional)*

No longer needed to look up the calendar. It is still accepted so existing configurations keep working.

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: wirral_gov_uk
      args:
        address_value: "42037487"
```

```yaml
waste_collection_schedule:
  sources:
    - name: wirral_gov_uk
      args:
        postcode: "CH49 4NP"
        address_value: "000042037487"
```
