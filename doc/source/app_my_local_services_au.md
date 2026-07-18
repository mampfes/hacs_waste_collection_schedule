# App Backend of My Local Services

Support for schedules provided by [App Backend of My Local Services](https://www.localcouncils.sa.gov.au).

Source for App Backend of My Local Services.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: app_my_local_services_au
      args:
        lat: LAT
        lon: LON
```

### Configuration Variables

**lat**  
*(float) (required)*

**lon**  
*(float) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: app_my_local_services_au
      args:
        lat: '-37.1647585'
        lon: '139.7851318'
```
