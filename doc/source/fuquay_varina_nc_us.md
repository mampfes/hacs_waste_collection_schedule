# Fuquay-Varina, North Carolina

Support for schedules provided by [Fuquay-Varina, North Carolina](https://gis1.fuquay-varina.org/).

Source for Fuquay-Varina, NC waste collection via ArcGIS services

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: fuquay_varina_nc_us
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: fuquay_varina_nc_us
      args:
        street_address: 155 S Main St
```
