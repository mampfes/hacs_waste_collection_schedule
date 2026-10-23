# Grenchen (CH)

Support for schedules provided by [Grenchen (CH)](https://www.grenchen.ch).

Source for waste collection in Grenchen, Switzerland. Deprecated: use localcities_ch instead.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: grenchen_ch
      args:
        zone: ZONE
```

### Configuration Variables

**zone**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: grenchen_ch
      args:
        zone: Zone Ost
```

## How to get the source arguments

This source is deprecated. Please use 'localcities.ch' instead with municipality='grenchen' and municipality_id='3533'.
