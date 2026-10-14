# City of Cockburn

Support for schedules provided by [City of Cockburn](https://www.cockburn.wa.gov.au).

Source script for cockburn.wa.gov.au

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cockburn_wa_gov_au
      args:
        address: ADDRESS
        property_no: PROPERTY_NO
```

### Configuration Variables

**address**  
*(string) (optional)*

**property_no**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cockburn_wa_gov_au
      args:
        address: 23 Snowden St, Hammond Park WA 6164
```
