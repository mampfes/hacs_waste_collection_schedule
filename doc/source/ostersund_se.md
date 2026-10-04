# Östersunds kommun

Support for schedules provided by [Östersunds kommun](https://www.ostersund.se).

Source for Östersunds kommun waste collection schedule, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ostersund_se
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
    - name: ostersund_se
      args:
        address: "\xC5terg\xE5ngen 1"
```

## How to get the source arguments

Go to the collection search on [ostersund.se](https://www.ostersund.se/bygga-bo-klimat-och-miljo/avfall-och-atervinning/nar-kommer-sopbilen.html), search for your address and copy the street name and house number exactly as shown in the results list, e.g. 'Återgången 1'. Only single-family homes in Östersunds kommun are covered; apartment buildings and businesses are not listed.
