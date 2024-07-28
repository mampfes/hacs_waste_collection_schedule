
# Rotorua Lakes Council

[Source URL](https://rotorua.maps.arcgis.com/apps/webappviewer/index.html?id=7176f71a4ca34c16aa7dc7f942b919d5)

[API URL](https://gis.rdc.govt.nz/server/rest/services/Core/RdcServices/MapServer/125/query)

This source provides waste collection schedules for Rotorua Lakes Council. It uses the Rotorua Lakes Council's GIS API to fetch waste collection schedules based on the provided address.

## Configuration via `configuration.yaml`

To configure the source, add the following to your `configuration.yaml` file:

```yaml
waste_collection_schedule:
  sources:
    - name: rotorua_lakes_council_nz
      args:
        address: UNIQUE_ADDRESS
```
        
## Configuration Variables

-   **address** (string) (required): The address for which you want to retrieve the waste collection schedule.

## Example

An example configuration:

```yaml
waste_collection_schedule:
  sources:
    - name: rotorua_lakes_council_nz
      args:
        address: 1061 Haupapa St
```
