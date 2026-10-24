# Frederikshavn Forsyning

Support for schedules provided by [Frederikshavn Forsyning](https://www.forsyningen.dk).

Source for Frederikshavn Forsyning (Frederikshavn Kommune).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: forsyningen_dk
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: forsyningen_dk
      args:
        address: "Hj\xF8rringvej 10"
```

## How to get the source arguments

Enter your address as the address search on https://renovation.forsyningen.dk/minside/Tomningsinfo suggests it, e.g. 'Hjørringvej 10' or 'Knivholtvej 15, 1 (9900)'.
