# Győri Hulladékgazdálkodási Nonprofit Kft.

Support for schedules provided by [Győri Hulladékgazdálkodási Nonprofit Kft.](https://www.gyhg.hu).

Source script using GYHG API at https://gyhg.bluespot.hu/api

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: gyhg_hu
      args:
        city: CITY
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: gyhg_hu
      args:
        city: "\xC9cs"
        street: Ady Endre utca
        house_number: 1/A
```

## How to get the source arguments

Select the desired address on the https://www.gyhg.hu/hulladeknaptar#/ website. The town, street name, and house number must be entered in this integration in the exact same format as they appear there.
