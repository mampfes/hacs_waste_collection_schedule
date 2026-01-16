# Pireva - Piteå Renhållning & Vatten 

Support for schedules provided by [Pireva](https://www.pireva.se/tomningsschema/), serving the municipality of Piteå, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: pireva_se
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)* The address of the property to get the waste collection schedule for.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: pireva_se
      args:
        street_address: Kolugnsvägen 1 Räddningstjänsten Mf
```

## How to get the source argument

The source argument is the address to the house with waste collection. The address can be tested 
[here](https://www.pireva.se/tomningsschema/) and should perfectly match the autocompletion/suggestion of the website.
