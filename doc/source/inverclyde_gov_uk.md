# Inverclyde Council

Support for schedules provided by [Inverclyde Council](https://www.inverclyde.gov.uk).

Source for Inverclyde Council, UK, waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: inverclyde_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
```

### Configuration Variables

**postcode**  
*(string) (required)*

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: inverclyde_gov_uk
      args:
        postcode: PA16 0FG
        address: 1 Findhorn Crescent
```

## How to get the source arguments

Visit https://maps.inverclyde.gov.uk/noticeboard8/noticeboard.aspx, search for your postcode and note down your address exactly as it is shown in the address list, e.g. '10 St John's Road'.
