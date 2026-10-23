# Roslagsvatten

Support for schedules provided by [Roslagsvatten](https://roslagsvatten.se).

Source for Roslagsvatten waste collection (Österåker, Vaxholm and Ekerö).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: roslagsvatten_se
      args:
        street_address: STREET_ADDRESS
        municipality: MUNICIPALITY
```

### Configuration Variables

**street_address**  
*(string) (required)*

**municipality**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: roslagsvatten_se
      args:
        street_address: "Andromedav\xE4gen 1, \xC5kersberga"
        municipality: osteraker
```

## How to get the source arguments

Enter the address as the Roslagsvatten schedule search writes it, street and number followed by the locality, e.g. `Andromedavägen 1, Åkersberga`, and pick your municipality.
