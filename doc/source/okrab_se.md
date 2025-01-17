# Ökrab Sophämntning

Support for schedules provided by [Ökrab](https://www.okrab.se/hamtning/tomningskalender/), serving the municipality of Simrishamn and Tomelilla, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: okrab_se
      args:
        address: STREET_ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: okrab_se
      args:
        address: SKOLGATAN 1, S:T OLOF
```

## How to get the source argument

The source argument is the address to the house with waste collection. The address can be tested [here](https://www.okrab.se/hamtning/tomningskalender).
