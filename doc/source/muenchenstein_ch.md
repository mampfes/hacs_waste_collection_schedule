# Münchenstein

Support for schedules provided by [Münchenstein](https://www.muenchenstein.ch).

Source for Muenchenstein waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: muenchenstein_ch
      args:
        waste_district: WASTE_DISTRICT
```

### Configuration Variables

**waste_district**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: muenchenstein_ch
      args:
        waste_district: Abfuhrkreis Ost
```

## How to get the source arguments

Enter your waste district, Abfuhrkreis Ost or Abfuhrkreis West, or its ID: 491 for Ost, 492 for West.
