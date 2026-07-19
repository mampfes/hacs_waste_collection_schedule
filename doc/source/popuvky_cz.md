# Popůvky

Support for waste collection schedules provided by [Obec Popůvky](https://www.popuvky.cz/obec/terminy-svozu/), Czech Republic.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: popuvky_cz
      args:
        place: PLACE
```

### Configuration Variables

**place**  
*(String) (required)*

The collection route/area exactly as listed on the official calendar page. Currently:

- `Popůvky (Brno-venkov)`
- `Popůvky - chatová oblast`

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: popuvky_cz
      args:
        place: Popůvky (Brno-venkov)
```

## How to get the source argument

Open the [collection calendar page](https://www.popuvky.cz/obec/terminy-svozu/) and note which collection route matches your address: `Popůvky (Brno-venkov)` for the village itself, or `Popůvky - chatová oblast` for the cottage/recreational area.

## Bin types returned

| Provider description  | Returned type          | Icon                      |
|------------------------|-------------------------|---------------------------|
| Komunální odpad        | Komunální odpad         | `Icons.GENERAL_WASTE`     |
| Plasty od domu         | Plasty od domu          | `Icons.PLASTIC_PACKAGING` |
| Papír                  | Papír                   | `Icons.PAPER`             |
| Sklo                   | Sklo                    | `Icons.GLASS`             |
| BIO odpad od domu      | BIO odpad od domu       | `Icons.ORGANIC`           |
