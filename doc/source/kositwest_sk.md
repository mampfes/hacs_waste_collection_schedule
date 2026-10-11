# KOSIT WEST

Support for schedules provided by [KOSIT WEST](https://kositwest.sk/sluzby/zber-komunalneho-odpadu-a-triedenych-zloziek-z-obci-a-samosprav/harmonogramy-zberu-odpadu-v-obciach/).

Source for KOSIT WEST waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kositwest_sk
      args:
        town: TOWN
```

### Configuration Variables

**town**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kositwest_sk
      args:
        town: Vieska
```

## How to get the source arguments

Find your town on the KOSIT WEST website and enter it exactly as it appears in the link.
