# Älvsbyns Energi

Support for schedules provided by [Älvsbyns Energi](https://www.alvsbynsenergi.se/).

Waste collection schedule for Älvsbyns Energi, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: alvsbyns_energi_se
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
    - name: alvsbyns_energi_se
      args:
        address: Storgatan 24
```

## How to get the source arguments

Enter the street address and house number as shown by the address search at https://www.alvsbynsenergi.se/ (for example, Storgatan 24).
