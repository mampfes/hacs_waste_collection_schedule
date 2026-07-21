# Marktgemeinde Pernitz

Support for waste collection schedules provided by [Marktgemeinde Pernitz](https://www.pernitz.gv.at), Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: pernitz_gv_at
      args:
        rayon: RAYON
```

### Configuration Variables

**rayon**
*(integer) (required)*

The general waste (Restmüll) collection zone, `1` or `2`, that your street belongs to. Biomass (Biotonne), yellow bag (Gelber Sack), yellow container (Gelber Container) and paper collection dates are the same for both zones.

Check <https://www.pernitz.gv.at/muellabfuhr/> under "Definition Rayon 1" / "Definition Rayon 2" for the list of streets belonging to each zone.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: pernitz_gv_at
      args:
        rayon: 1
```

## How to get the source arguments

Open <https://www.pernitz.gv.at/muellabfuhr/>, expand "Definition Rayon 1" and "Definition Rayon 2" and find your street to determine which zone (`1` or `2`) to use for `rayon`.

Note: the "Abholung von Restmüll und gelbem Sack vom Waxeneck" special collection (a small number of addresses in the Waxeneck area) is not currently supported by this source.
