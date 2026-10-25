# Causeway Coast and Glens Borough Council

Support for schedules provided by [Causeway Coast and Glens Borough Council](https://causewaycoastandglens.gov.uk).

Source for Causeway Coast and Glens Borough Council black and blue bin calendars.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: causewaycoastandglens_gov_uk
      args:
        area: AREA
        collection_day: COLLECTION_DAY
```

### Configuration Variables

**area**  
*(string) (required)*

**collection_day**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: causewaycoastandglens_gov_uk
      args:
        area: Coleraine
        collection_day: Tuesday
```

## How to get the source arguments

Choose your former council area (Ballymoney, Coleraine, Limavady or Moyle) as on https://causewaycoastandglens.gov.uk/live/bins-and-recycling/bin-collections/collection-calendars, and your normal bin collection day. Collection changes for bank holidays are announced by the council separately and are not part of the calendar.
