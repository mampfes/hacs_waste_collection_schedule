# LSR (Landskrona - Svalövs Renhållning)

Support for schedules provided by [LSR](https://www.lsr.nu/hamtningsschema/), serving the municipalities of Landskrona and Svalöv, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: lsr_nu
      args:
        street_address: STREET_NAME, CITY
```

### Configuration Variables

**street_address**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: lsr_nu
      args:
        street_address: Saxtorpsvägen 115, Annelöv
```

## How to get the source argument

The source argument is the address to the house with waste collection. The address can be tested [here](https://www.lsr.nu/hamtningsschema/).
