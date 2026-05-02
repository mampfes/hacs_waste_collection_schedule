# Greater Dandenong City Council

Support for schedules provided by [Greater Dandenong City Council](https://www.greaterdandenong.vic.gov.au/find-my-bin-day).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: greaterdandenong_vic_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)* Street address

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: greaterdandenong_vic_gov_au
      args:
        address: 45 Ardgower Road Noble Park
```

## How to get the source arguments

Visit the [Find My Bin Day](https://www.greaterdandenong.vic.gov.au/find-my-bin-day) page and search for your address.

Collection types:

- **Waste** — collected weekly
- **Recycling** — collected fortnightly
- **Garden** — collected fortnightly
- **Street Sweep** — scheduled date
