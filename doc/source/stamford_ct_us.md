# City of Stamford, CT

Support for schedules provided by [City of Stamford, CT](https://www.stamfordct.gov/government/operations/recycling-and-sanitation/about/recycling-and-garbage-schedule).

Source for the City of Stamford, CT garbage and recycling pickup day lookup.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stamford_ct_us
      args:
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stamford_ct_us
      args:
        street: Parker Ave
```

## How to get the source arguments

Enter your street name without house number. Enter house_number separately when pickup days vary along the street; the error lists the available ranges. Both numbered ranges and the council's ALL designation are supported. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.
