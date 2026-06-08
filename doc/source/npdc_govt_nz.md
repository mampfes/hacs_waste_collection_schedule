# New Plymouth District Council

Support for schedules provided by [New Plymouth District Council](https://www.npdc.govt.nz).

## Configuration via `configuration.yaml`

```yaml
waste_collection_schedule:
  sources:
    - name: npdc_govt_nz
      args:
        address: YOUR_ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

Your street address within the New Plymouth District. Use the address as it appears in the NPDC address search (e.g. `107 Coronation Avenue`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: npdc_govt_nz
      args:
        address: 107 Coronation Avenue
```

## How to find your address

Enter your address on the [NPDC bin collection schedule page](https://www.npdc.govt.nz/zero-waste/recycling-and-rubbish-collection/your-bin-collection-schedule/) to confirm it is recognised. Use the same address string in your configuration.

## Collection types

| Type | Frequency | Notes |
|---|---|---|
| Glass and Landfill | Fortnightly | Alternates with Recycling |
| Recycling | Fortnightly | Alternates with Glass and Landfill |
| Food Scraps | Weekly | Every collection week |

Properties are assigned to either a **Blue** or **Yellow** collection week, which determines which fortnight Glass and Landfill is collected versus Recycling.
