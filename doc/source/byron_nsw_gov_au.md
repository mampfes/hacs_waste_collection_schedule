# Byron Shire Council

Support for schedules provided by [Byron Shire Council](https://www.byron.nsw.gov.au/Residential-Services/Waste-Recycling/Bin-Collection-Services/Bin-Collection-Schedules).

Source for Byron Shire Council, NSW, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: byron_nsw_gov_au
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
    - name: byron_nsw_gov_au
      args:
        address: 120 Jonson St, Byron Bay
```

## How to get the source arguments

This source is deprecated. Use recyclecoach_com with street set to your address, project_id 592 and district_id BYSC. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.
