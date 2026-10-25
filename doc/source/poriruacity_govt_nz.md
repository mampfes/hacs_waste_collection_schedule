# Porirua City

Support for schedules provided by [Porirua City](https://poriruacity.govt.nz/).

Source for Porirua City.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: poriruacity_govt_nz
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
    - name: poriruacity_govt_nz
      args:
        address: 6 Ration Lane Whitby, Porirua City 5024
```

## How to get the source arguments

Enter your address as shown at https://poriruacity.govt.nz/services/rubbish-and-recycling/recycling-calendar/. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.
