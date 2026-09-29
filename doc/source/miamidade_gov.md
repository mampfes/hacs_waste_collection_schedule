# Miami-Dade County

Support for schedules provided by [Miami-Dade County](https://www.miamidade.gov/global/solidwaste/home.page).

Source for Miami-Dade County garbage and recycling pickup.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: miamidade_gov
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: miamidade_gov
      args:
        address: 9232 SW 148th Ct, Miami, FL 33196
```

## How to get the source arguments

Enter your full street address including city, state and ZIP code (e.g. '9232 SW 148th Ct, Miami, FL 33196'). It is matched against the county's Garbage and Recycling Pickup Days routes (https://gisweb.miamidade.gov/garbageandrecyclingpickupdays/).
