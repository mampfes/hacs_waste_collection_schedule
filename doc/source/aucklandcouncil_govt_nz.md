# Auckland Council

Support for schedules provided by [Auckland Council](https://www.aucklandcouncil.govt.nz).

Source for Auckland Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: aucklandcouncil_govt_nz
      args:
        area_number: AREA_NUMBER
```

### Configuration Variables

**area_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: aucklandcouncil_govt_nz
      args:
        area_number: '12342453293'
```

## How to get the source arguments

Search for your address on the council's collection-day page (https://www.aucklandcouncil.govt.nz/en/rubbish-recycling/rubbish-recycling-collections/rubbish-recycling-collection-days.html). The area number is the number in the address of the result page, e.g. 12342453293 in .../rubbish-recycling-collection-days/12342453293.html. Since the v3 pipeline migration, waste types use canonical, localised names. Update filters, automations and customisations using the old labels.
