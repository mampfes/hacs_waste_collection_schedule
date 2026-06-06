# Abilene, TX

Support for schedules provided by [City of Abilene Solid Waste & Recycling](https://abilenetx.gov/426/Solid-Waste-Recycling).

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

Full street address including city and state.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: abilene_tx_us
      args:
        address: 3601 Chimney Rock Rd, Abilene, TX
```

## How to get the source arguments

Use your full street address including city and state. This source returns:

- **Trash** — twice-weekly residential trash pickup (Monday/Thursday or Tuesday/Friday depending on your zone).
- **Yard Waste** — monthly curbside brush and bulky pickup (odd months only; the specific week of month varies by zone).
