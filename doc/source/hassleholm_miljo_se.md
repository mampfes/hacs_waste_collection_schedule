# Hässleholm Miljö

Support for schedules provided by [Hässleholm Miljö](https://hassleholmmiljo.se), serving the municipality of Hässleholm, Sweden.

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

The address alias from the Hässleholm Miljö waste calendar URL. See below for how to find your alias.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hassleholm_miljo_se
      args:
        alias: hmab-tyringevaegen-24-finja
```

## How to get the source argument

1. Go to [https://hassleholmmiljo.se/privat/sophamtning/tomningskalender](https://hassleholmmiljo.se/privat/sophamtning/tomningskalender).
2. Enter your street address in the search box and select your address from the suggestions.
3. After the calendar loads, copy the `alias` value from the URL — it looks like `?alias=hmab-yoursteet-number-city`.

For example, for the address "Tyringevägen 24, Finja" the URL becomes:
`https://hassleholmmiljo.se/privat/sophamtning/tomningskalender?alias=hmab-tyringevaegen-24-finja`

The alias is `hmab-tyringevaegen-24-finja`.
