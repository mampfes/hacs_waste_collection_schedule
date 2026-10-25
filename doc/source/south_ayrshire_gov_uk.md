# South Ayrshire Council

Support for schedules provided by [South Ayrshire Council](https://www.south-ayrshire.gov.uk).

Source for south-ayrshire.gov.uk services for South Ayrshire.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: south_ayrshire_gov_uk
      args:
        postcode: POSTCODE
        uprn: UPRN
```

### Configuration Variables

**postcode**  
*(string) (required)*

**uprn**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: south_ayrshire_gov_uk
      args:
        postcode: KA7 3XH
        uprn: '141030966'
```

## How to get the source arguments

Enter your postcode and the property UPRN from the council's bin collection form. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.
