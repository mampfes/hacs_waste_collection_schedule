# Hässleholm Miljö

Support for schedules provided by [Hässleholm Miljö](https://hassleholmmiljo.se).

Source for waste collection schedules from Hässleholm Miljö, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hassleholm_miljo_se
      args:
        alias: ALIAS
```

### Configuration Variables

**alias**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hassleholm_miljo_se
      args:
        alias: hmab-tyringevaegen-24-finja
```

## How to get the source arguments

Open https://hassleholmmiljo.se/privat/sophamtning/tomningskalender, search for your address and select it. Copy the `alias` value from the URL (`?alias=hmab-...`), for example `hmab-tyringevaegen-24-finja`.
