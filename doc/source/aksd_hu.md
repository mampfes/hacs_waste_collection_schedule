# AKSD Debrecen

Support for schedules provided by [AKSD Debrecen](https://www.aksd.hu).

Source for waste collection in Debrecen, Hungary, provided by A.K.S.D. Kft.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: aksd_hu
      args:
        street: STREET
```

### Configuration Variables

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: aksd_hu
      args:
        street: Kinizsi utca
```

## How to get the source arguments

Enter the street name exactly as it appears in the street search at https://www.aksd.hu/hulladeknaptar (e.g. `Kinizsi utca`). Upper/lower case and accents are ignored.
