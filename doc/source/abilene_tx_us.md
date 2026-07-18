# Abilene, TX

Support for schedules provided by [Abilene, TX](https://abilenetx.gov/426/Solid-Waste-Recycling).

Source for Abilene, TX solid waste and yard waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abilene_tx_us
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
    - name: abilene_tx_us
      args:
        address: 3601 Chimney Rock Rd, Abilene, TX
```

## How to get the source arguments

Enter your full street address including city and state (e.g. '3601 Chimney Rock Rd, Abilene, TX').
