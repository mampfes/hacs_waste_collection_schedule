# City of Greater Shepparton

Support for schedules provided by [City of Greater Shepparton](https://greatershepparton.com.au/animals-environment-and-waste/waste-and-recycling/kerbside-collection).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: greatershepparton_com_au
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

Street address within the City of Greater Shepparton.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: greatershepparton_com_au
      args:
        street_address: 161 Welsford Street, Shepparton
```

## How to get the source arguments

Enter your full street address, including suburb, e.g. `161 Welsford Street, Shepparton`. Use full street-type words (`Street`, `Road`, `Square`) rather than abbreviations (`St`, `Rd`, `Sq`) - the council's address lookup only matches on the full word. You can check your address resolves correctly using the [council's own bin lookup tool](https://greatershepparton.com.au/animals-environment-and-waste/waste-and-recycling/kerbside-collection) first.

## Bin types returned

| Bin | Returned type | Icon | Cadence |
|---|---|---|---|
| Red-lid | General Waste | `Icons.GENERAL_WASTE` | Fortnightly |
| Yellow-lid | Recycling | `Icons.RECYCLING` | Fortnightly |
| Green-lid | Organics | `Icons.ORGANIC` | Weekly |
| Purple-lid | Glass | `Icons.GLASS` | Every 4 weeks |

## Known limitation

The council temporarily shifts collection days by one for some zones around Christmas/New Year (the exact dates and affected zones vary by year and aren't published as data - they're embedded in the council's own scheduling logic). This source does not model that temporary shift, so collection dates may be off by up to a day for roughly two weeks spanning the holiday period. Outside that window, dates are fetched live and should always match the council's own lookup tool.
