# Basel-Stadt

Support for schedules provided by [data.bs.ch](https://data.bs.ch), Switzerland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: data_bs_ch
      args:
        zone: B
```

### Configuration Variables

**zone** *(string) (required)*: Your waste collection zone. Available values: `A`, `B`, `C`, `D`, `E`, `F`, `G`, `H`, `GUF`.

Find your zone on the [Basel-Stadt zone map](https://map.geo.bs.ch/?lang=de&baselayer_ref=Grundkarte%20farbig&map_x=2611169.25&map_y=1267226.5&map_zoom=5&tree_group_layers_Abfuhrzonen_Basel=AF_AbfuhrzoneGemeindeBasel&tree_groups=Abfuhrzonen_Basel).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: data_bs_ch
      args:
        zone: "B"
```
