# City of Cockburn (WA)

Support for schedules provided by [City of Cockburn (WA)](https://www.cockburn.wa.gov.au/Environment-and-Waste/Rubbish-Waste-and-Recycling/Bin-Collections).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cockburn_wa_gov_au
      args:
        address: ADDRESS

```

### Configuration Variables

**address**
*(string) (required)*

**property_no**
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cockburn_wa_gov_au
      args:
        address: 1 Eucalyptus Dr Hammond Park
```

```yaml
waste_collection_schedule:
  sources:
    - name: cockburn_wa_gov_au
      args:
       property_no: 6025742

## How to get the source arguments

Visit the [City of Cockburn (WA)](https://www.cockburn.wa.gov.au/Environment-and-Waste/Rubbish-Waste-and-Recycling/Bin-Collections) page and search for your address.  The arguments should exactly match the results shown for Suburb and Street and the number portion of the Property. You can also obtain your property number from your council rates notice.
