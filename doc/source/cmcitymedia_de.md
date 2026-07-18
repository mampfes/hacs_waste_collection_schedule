# CM City Media - Müllkalender

Support for schedules provided by [CM City Media - Müllkalender](https://cmcitymedia.de).

Source script for cmcitymedia.de

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cmcitymedia_de
      args:
        hpid: HPID
        realmid: REALMID
        district: DISTRICT
```

### Configuration Variables

**hpid**  
*(string) (required)*

**realmid**  
*(string) (optional)*

**district**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cmcitymedia_de
      args:
        hpid: 415
        district: 1371
```
