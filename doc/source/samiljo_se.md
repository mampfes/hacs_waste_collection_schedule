# Samverkan Återvinning Miljö (SÅM)

Support for schedules provided by [Samverkan Återvinning Miljö (SÅM)](https://samiljo.se/avfallshamtning/hamtningskalender/), serving the municipality of Gislaved, Gnosjö, Vaggeryd and Värnamo, Sweden. 

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: samiljo_se
      args:
        street: STREET_NAME
        city: CITY_NAME
```

### Configuration Variables

**street**
*(string) (required)*

**city**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: samiljo_se
      args:
        street: Storgatan 1
        city: Burseryd
```


## How to get the source argument

The source argument is the street including number and the city to the house with waste collection.
The address can be tested [here](https://samiljo.se/avfallshamtning/hamtningskalender/).
