# A-Region

Support for schedules provided by [A-Region](https://www.a-region.ch).

Source for A-Region, Switzerland waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: a_region_ch
      args:
        municipality: MUNICIPALITY
        district: DISTRICT
```

### Configuration Variables

**municipality**  
*(string) (required)*

**district**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: a_region_ch
      args:
        municipality: Andwil
```
