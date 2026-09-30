# VMAB

Support for schedules provided by [VMAB](https://vmab.se).

Source for Västblekinge Miljö AB waste collection.

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

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: vmab_se
      args:
        street_address: "Rosenborgsv\xE4gen 35, Karlshamn"
```

## How to get the source arguments

Enter your street address and city, separated by a comma, exactly as they appear when you search for your address on https://vmab.se/privat/vmabs-tomningskalender, e.g. `Rosenborgsvägen 35, Karlshamn`. Only houses with the four-slot bins (Max 1 and Max 2) are covered, not apartment buildings.
