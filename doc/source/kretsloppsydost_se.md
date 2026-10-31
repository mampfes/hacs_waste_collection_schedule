# Kretslopp Sydost

Support for schedules provided by [Kretslopp Sydost](https://kretsloppsydost.se).

Source for Kretslopp Sydost (Kalmar, Mörbylånga, Nybro, Oskarshamn, Sävsjö, Torsås, Uppvidinge and Vetlanda).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kretsloppsydost_se
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
    - name: kretsloppsydost_se
      args:
        street_address: "H\xE4gnev\xE4gen 1, S\xE4vsj\xF6"
```

## How to get the source arguments

Enter your street address and place as the search on kretsloppsydost.se lists it, for example 'Hägnevägen 1, Sävsjö'. This replaces the 'kretslopp-sydost' provider of the EDP Future source, which leaves out the second bin (Kärl 2).
