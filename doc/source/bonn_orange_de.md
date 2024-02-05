# Bonn Orange

Support for schedules provided by [Bonn Orange](https://www.bonnorange.de/), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bonn_orange_de
      args:
        street: STREET
        house_number: HNR
        address_suffix: HNR_SUFFIX
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(integer) (required)*

**address_suffix**  
*(string) (optional) (default: "")*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bonn_orange_de
      args:
        street: "Baumschulallee"
        house_number: 43
        address_suffix: "A"
```

## How to get the source arguments

These values are the location you want to query for. Make sure, the writing is exactly as it is on [https://www.bonnorange.de/service/privatpersonen/abfuhrtermine/termine](https://www.bonnorange.de/service/privatpersonen/abfuhrtermine/termine). Typos may result in an Exception. As `house_number` expects a numeric input, address suffixes have to be provided via the `address_suffix` argument.
