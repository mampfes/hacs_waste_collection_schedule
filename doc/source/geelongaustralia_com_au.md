# City of Greater Geelong

Support for schedules provided by [City of Greater Geelong](https://www.geelongcity.vic.gov.au/).

Source City of Greater Geelong rubbish collection

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: geelongaustralia_com_au
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
    - name: geelongaustralia_com_au
      args:
        address: 155 Mercer Street Geelong 3220
```

## How to get the source arguments

Enter your address exactly as accepted by the council's calendar search: https://www.geelongaustralia.com.au/recycling/calendar.aspx. Since the v3 pipeline migration, waste types use canonical, localised names. Update filters, automations and customisations using the old labels.
