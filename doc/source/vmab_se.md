# Västblekinge Miljö AB (VMAB)

Support for schedules provided by [Västblekinge Miljö AB (VMAB)](https://vmab.se/privat/vmabs-tomningskalender/), serving the municipalities of Karlshamn, Sölvesborg, and Olofström in Blekinge, Sweden.

Note that this calendar service only applies to customers with "Fyrfack" bins (regular residential houses). It does not work for apartment buildings or municipal/state service locations.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: vmab_se
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

The street address including city, separated by a comma.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: vmab_se
      args:
        street_address: Rosenborgsvägen 35, Karlshamn
```

## How to get the source argument

The source argument is the address to the house with waste collection. The address can be looked up at [vmab.se/privat/vmabs-tomningskalender](https://vmab.se/privat/vmabs-tomningskalender/).
