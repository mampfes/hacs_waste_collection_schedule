# Recycle Coach

Support for schedules provided by [Recycle Coach](https://recyclecoach.com).

Source loader for recyclecoach.com

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: recyclecoach_com
      args:
        street: STREET
        city: CITY
        state: STATE
        project_id: PROJECT_ID
        district_id: DISTRICT_ID
        zone_id: ZONE_ID
```

### Configuration Variables

**street**  
*(string) (optional)*

**city**  
*(string) (optional)*

**state**  
*(string) (optional)*

**project_id**  
*(string) (optional)*

**district_id**  
*(string) (optional)*

**zone_id**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: recyclecoach_com
      args:
        street: 2242 grinstead drive
        city: louisville
        state: KY
```
