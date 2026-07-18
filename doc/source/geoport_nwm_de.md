# Landkreis Nordwestmecklenburg

Support for schedules provided by [Landkreis Nordwestmecklenburg](https://www.geoport-nwm.de).

Source for Landkreis Nordwestmecklenburg.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: geoport_nwm_de
      args:
        district: DISTRICT
```

### Configuration Variables

**district**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: geoport_nwm_de
      args:
        district: "R\xFCting"
```
