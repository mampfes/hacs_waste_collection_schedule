# VA Syd Sophämntning

Support for schedules provided by [VA Syd Sophämntning](https://www.vasyd.se).

Source for VA Syd waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: vasyd_se
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: vasyd_se
      args:
        street_address: "Industrigatan 13, Arl\xF6v"
```

## How to get the source arguments

Enter the address as VA Syd lists it: '<street> <number>, <city>', for example 'Storgatan 1, Malmö'. The first address the search finds is used, so include the city to avoid a wrong match.
