# Bamberg (City/Stadt)

Support for schedules provided by [Bamberg (City/Stadt)](https://www.stadt.bamberg.de), serving the city of Bamberg, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: stadt_bamberg_de
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
    - name: stadt_bamberg_de
      args:
        street: "Egelseestraße"
        house_number: 114
        address_suffix: "a"
```

```yaml
waste_collection_schedule:
  sources:
    - name: stadt_bamberg_de
      args:
        street: Gartenstraße
        house_number: 2
```

## How to get the source arguments

These values are the location you want to query for. Make sure, they are spelled exactly as on <https://www.stadt.bamberg.de/B%C3%BCrgerservice/%C3%84mter/Bamberg-Service-/Abfallwirtschaft/Abfuhrtermine/>. Typos may result in an Exception. As `house_number` expects a numeric input, address suffixes have to be provided via the `address_suffix` argument.
