# Shire of Dardanup

Support for schedules provided by [Shire of Dardanup](https://www.dardanup.wa.gov.au).

Source for Shire of Dardanup (WA) waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: dardanup_wa_gov_au
      args:
        street: STREET
        service_area: SERVICE_AREA
        collection_day: COLLECTION_DAY
```

### Configuration Variables

**street**  
*(string) (optional)*

**service_area**  
*(string) (optional)*

**collection_day**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: dardanup_wa_gov_au
      args:
        street: Hale Street
        service_area: Area 1
```

## How to get the source arguments

Find your street/townsite and service area in the current waste guide linked from https://www.dardanup.wa.gov.au/our-services/waste-and-recycling/find-your-bin-day.aspx. Enter street and service_area; collection_day can specify the published weekday directly. Streets spanning Area 1 and Area 2 require service_area. Replace the old recycling_in_even_week argument with service_area: the published calendar now supplies the recycling phase and holiday replacements, including across ISO week 53. Rural two-bin services have no FOGO collection. Dates stop at the end of the published guide, with no projection beyond it. Since the v3 migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.
