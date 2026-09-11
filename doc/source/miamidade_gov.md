# Miami-Dade County

Support for garbage and recycling schedules provided by [Miami-Dade County](https://www.miamidade.gov/global/solidwaste/home.page), Florida, USA.

This source uses Miami-Dade County's public ArcGIS services. It can either look up your route polygons from a service address, or use garbage and recycling route codes directly.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: miamidade_gov
      args:
        address: "111 NW 1st St, Miami, FL"
```

Alternatively, configure one or both route codes:

```yaml
waste_collection_schedule:
  sources:
    - name: miamidade_gov
      args:
        garbage_route: "5206"
        recycling_route: "32A385"
```

### Configuration Variables

**address**  
*(string) (optional)*: Miami-Dade service address. Optional if route codes are provided.

**garbage_route**  
*(string) (optional)*: Garbage route code. Optional if `address` is provided.

**recycling_route**  
*(string) (optional)*: Recycling route code. Optional if `address` is provided.

At least one of `address`, `garbage_route`, or `recycling_route` is required.

## How to find your route codes

Open Miami-Dade's official Garbage and Recycling Pickup Days lookup and search for your service address:

<https://gisweb.miamidade.gov/garbageandrecyclingpickupdays/>

Use the displayed Garbage Route and Recycling Route values in the source configuration.
