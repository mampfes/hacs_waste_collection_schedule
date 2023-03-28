# Uppsala Vatten och Avfall AB

Support for schedules provided by [Uppsala Vatten och Avfall AB](https://www.uppsalavatten.se), serving the municipality of Uppsala. 

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: uppsalavatten_se
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
    - name: uppsalavatten_se
      args:
        street: SADELVÄGEN 1
        city: BJÖRKLINGE
```


## How to get the source argument

The source argument is the street including number and the city to the house with waste collection.
The address can be tested [here](https://www.uppsalavatten.se/sjalvservice/hamtningar-och-berakningar/dag-for-sophamtning-och-slamtomning).



