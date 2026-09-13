# KOSIT WEST

You can find support for KOSIT WEST waste collection at [https://kositwest.sk/sluzby/zber-komunalneho-odpadu-a-triedenych-zloziek-z-obci-a-samosprav/harmonogramy-zberu-odpadu-v-obciach/](https://kositwest.sk/sluzby/zber-komunalneho-odpadu-a-triedenych-zloziek-z-obci-a-samosprav/harmonogramy-zberu-odpadu-v-obciach/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kositwest_sk
      args:
        town: Vieska
```

## Configuration parameters

- **town**: Town name as displayed on the kositwest.sk website.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kositwest_sk
      args:
        town: Michal na Ostrove
```

## HOW TO GET ARGUMENTS

Find your town on the [KOSIT WEST website](https://kositwest.sk/sluzby/zber-komunalneho-odpadu-a-triedenych-zloziek-z-obci-a-samosprav/harmonogramy-zberu-odpadu-v-obciach/) and enter it exactly as it appears in the link.
