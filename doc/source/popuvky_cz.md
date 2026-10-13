# Popůvky

Support for schedules provided by [Popůvky](https://www.popuvky.cz/obec/terminy-svozu/).

Source for the municipal waste collection calendar of Popůvky, Czech Republic.

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
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: popuvky_cz
      args:
        place: "Pop\u016Fvky (Brno-venkov)"
```

## How to get the source arguments

Open the collection calendar page and note which collection route matches your address: 'Popůvky (Brno-venkov)' for the village itself, or 'Popůvky - chatová oblast' for the cottage/recreational area.
