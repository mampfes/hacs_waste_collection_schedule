# TAMAX (Gmina Radziemice)

Support for schedules provided by [TAMAX (Gmina Radziemice)](https://www.tamax.net.pl).

Source for TAMAX household waste collection in Gmina Radziemice.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tamax_net_pl
      args:
        area: AREA
```

### Configuration Variables

**area**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: tamax_net_pl
      args:
        area: "B\u0142ogocice, K\u0105ty, Kowary, Radziemice, Wola Gruszowska"
```

## How to get the source arguments

On https://www.tamax.net.pl/harmonogramy/ find Gmina Radziemice and select the village group printed on your household calendar. Only these three Radziemice household tables are supported; other municipalities, apartment blocks and business calendars use different layouts. In particular, the Racławice download is for businesses. Ash (Popiół paleniskowy) is classified as Other and keeps its original label. The combined bulky collection also accepts electronics and textiles. Tyres have no separate canonical type.
