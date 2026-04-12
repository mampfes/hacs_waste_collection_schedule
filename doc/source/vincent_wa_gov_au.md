# City of Vincent

Support for schedules provided by [City of Vincent](https://www.vincent.wa.gov.au/your-home/waste-recycling/your-bin-day.aspx).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: vincent_wa_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: vincent_wa_gov_au
      args:
        address: 8 Kadina St, North Perth WA 6006
```

## How to get the source arguments

Visit the [City of Vincent Bin Day](https://www.vincent.wa.gov.au/your-home/waste-recycling/your-bin-day.aspx) page and search for your address in the map. Use the same address format, e.g. "8 Kadina St, North Perth WA 6006".
