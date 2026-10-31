# Vogel Disposal Service

Support for schedules provided by [Vogel Disposal Service](https://www.vogeldisposal.com/).

Residential trash and recycling collection schedules for Vogel Disposal Service (Mars, PA).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: vogeldisposal_com
      args:
        municipality: MUNICIPALITY
        address: ADDRESS
```

### Configuration Variables

**municipality**  
*(string) (required)*

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: vogeldisposal_com
      args:
        municipality: BUTLER TWP, BUTLER COUNTY
        address: 1002 TUDOR DR
```

## How to get the source arguments

Enter your municipality and street address. Exact spelling is not required: a rough municipality (for example 'butler twp') and a partial street address (for example '1002 tudor') are matched automatically. If the input matches more than one place, the matching options are shown so you can pick the right one. Since the v3 pipeline migration, waste types use canonical, localised names. Update filters, automations and customisations using the old labels.
