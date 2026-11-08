# Homewood Disposal Service (NuWay)

Support for schedules provided by [Homewood Disposal Service (NuWay)](https://mydisposal.com).

Source for Homewood Disposal Service (also known as NuWay Disposal), Chicagoland and Northwest Indiana.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mydisposal_com
      args:
        address: ADDRESS
        municipality: MUNICIPALITY
        recycling_date: RECYCLING_DATE
```

### Configuration Variables

**address**  
*(string) (required)*

**municipality**  
*(string) (required)*

**recycling_date**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mydisposal_com
      args:
        address: 14240 W 151st St, Homer Glen, IL 60491
        municipality: Homer Glen
```

## How to get the source arguments

Enter your street address and pick your municipality; the pickup day comes from the map on your town's mydisposal.com page. Most towns collect recycling every other week: enter the date (YYYY-MM-DD) of any recycling pickup to get recycling dates, or leave it empty to skip recycling. Homer Glen and Lockport Township recycle weekly and need no date.
