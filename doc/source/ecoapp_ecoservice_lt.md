# Ecoservice atliekos

Support for schedules provided by [Ecoservice atliekos](https://ecoservice.lt/).

Source for UAB "Ecoservice".

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ecoapp_ecoservice_lt
      args:
        waste_object_ids: WASTE_OBJECT_IDS
```

### Configuration Variables

**waste_object_ids**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ecoapp_ecoservice_lt
      args:
        waste_object_ids: '''13-L-115261'', 13-P-505460,13-S-500496'
```

## How to get the source arguments

Enter the inventory number printed on the side of each container, separated by commas, e.g. 13-L-115261, 13-P-505460. You can check them in the schedule search on https://ecoservice.lt/grafikai/. Since the v3 pipeline migration, waste types use canonical, localised names. Update filters, automations and customisations using the old labels.
