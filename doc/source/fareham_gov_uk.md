# Fareham Borough Council

Support for schedules provided by [Fareham Borough Council](https://www.fareham.gov.uk).

Source for fareham.gov.uk

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: fareham_gov_uk
      args:
        road_name: ROAD_NAME
        postcode: POSTCODE
```

### Configuration Variables

**road_name**  
*(string) (required)*

**postcode**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: fareham_gov_uk
      args:
        road_name: Hunts pond road
        postcode: PO14 4PL
```

## How to get the source arguments

Enter your postcode and your road name as listed by the council, optionally with your house number in front (e.g. '203 Segensworth road'). Without a house number the collections of all matching properties on the road are combined.
