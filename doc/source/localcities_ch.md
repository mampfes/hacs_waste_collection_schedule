# localcities.ch

Support for schedules provided by [localcities.ch](https://www.localcities.ch).

Source for waste collection schedules from localcities.ch (Switzerland).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: localcities_ch
      args:
        municipality: MUNICIPALITY
        municipality_id: MUNICIPALITY_ID
        zone: ZONE
```

### Configuration Variables

**municipality**  
*(string) (required)*

**municipality_id**  
*(string) (required)*

**zone**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: localcities_ch
      args:
        municipality: volketswil
        municipality_id: '529'
        zone: Hegnau
```

## How to get the source arguments

Visit your municipality's page on localcities.ch. The municipality name and ID are in the URL (e.g. /de/entsorgung/volketswil/529). The zone is shown next to each waste collection entry on the calendar. If your municipality does not use zones, omit the zone parameter.
