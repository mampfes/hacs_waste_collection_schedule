# Taupō District Council

[Source URL](https://www.taupodc.govt.nz/property-and-rates/rubbish-and-recycling/kerbside-refuse-and-recycling-collection)

[Collection Day Map](https://taupo.maps.arcgis.com/apps/instant/lookup/index.html?appid=5a763f92dc6e4d09aa06fcdf5476591f)

This source retrieves weekly kerbside collection days for properties in the Taupō District, New Zealand. It queries the Taupō District Council's ArcGIS feature services to look up the collection day(s) for a given address.

## Configuration via `configuration.yaml`

```yaml
waste_collection_schedule:
  sources:
    - name: taupodc_govt_nz
      args:
        address: ADDRESS
```

## Configuration Variables

**address** (string) (required)
The full street address of the property, as listed in the Taupō District Council property database. Use the address as it appears in the [collection day map](https://taupo.maps.arcgis.com/apps/instant/lookup/index.html?appid=5a763f92dc6e4d09aa06fcdf5476591f) search, e.g. `9 Richmond Avenue Taupo`.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: taupodc_govt_nz
      args:
        address: 72 Wharewaka Road Taupo
```
