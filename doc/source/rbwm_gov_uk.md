# Windsor and Maidenhead

Support for schedules provided by [Windsor and Maidenhead](https://my.rbwm.gov.uk/).

Source for Windsor and Maidenhead.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: rbwm_gov_uk
      args:
        uprn: UPRN
        postcode: POSTCODE
```

### Configuration Variables

**uprn**  
*(string) (required)*

**postcode**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: rbwm_gov_uk
      args:
        postcode: SL4 4EN
        uprn: 100080381393
```
