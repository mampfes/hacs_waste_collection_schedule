# KOSIT EAST

Support for schedules provided by [KOSIT EAST](https://kositeast.sk).

Source for KOSIT EAST waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kositeast_sk
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
    - name: kositeast_sk
      args:
        town: Adidovce
```

## How to get the source arguments

Find your town on https://kositeast.sk/obyvatelia/harmonogram-zberu-odpadu-v-obciach/ and enter it exactly as it appears in the link.
