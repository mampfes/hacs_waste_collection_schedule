# KOSIT EAST

You can find support for KOSIT EAST waste collection at [https://kositeast.sk/obyvatelia/harmonogram-zberu-odpadu-v-obciach/](https://kositeast.sk/obyvatelia/harmonogram-zberu-odpadu-v-obciach/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kositeast_sk
      args:
        town: Adidovce
```

## Configuration parameters

- **town**: Town name as displayed on the kositeast.sk website.

## HOW TO GET ARGUMENTS

Find your town on [https://kositeast.sk/obyvatelia/harmonogram-zberu-odpadu-v-obciach/](https://kositeast.sk/obyvatelia/harmonogram-zberu-odpadu-v-obciach/) and enter it exactly as it appears in the link.
