# City of Yarra

Support for schedules provided by [City of Yarra](https://www.yarracity.vic.gov.au/residents/bins-waste-recycling-and-cleansing/recycling-and-rubbish/bin-collection), Victoria, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: yarracity_vic_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

Full street address within the City of Yarra, including suburb and postcode.

For a residential address you can keep the value out of source control by storing it in Home Assistant `secrets.yaml` and referencing it with `!secret`.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: yarracity_vic_gov_au
      args:
        address: 333 Bridge Road, Richmond VIC 3121
```

## How to get the source arguments

Use your address as you would enter it in the council's [bin collection lookup](https://www.yarracity.vic.gov.au/residents/bins-waste-recycling-and-cleansing/recycling-and-rubbish/bin-collection). Include the suburb and postcode for reliable matching.

Collection types returned:

- **Rubbish** — weekly
- **FOGO** (Food Organics and Garden Organics) — weekly, same day as Rubbish
- **Recycling** — fortnightly, same day as Rubbish
- **Glass** — every four weeks

A household without a FOGO bin can hide that type with the standard customisation:

```yaml
waste_collection_schedule:
  sources:
    - name: yarracity_vic_gov_au
      args:
        address: 333 Bridge Road, Richmond VIC 3121
      customize:
        - type: FOGO
          show: false
```

## Public holidays

Collections run as normal on public holidays except Good Friday and Christmas Day, when the collection happens one day later. The source applies this shift automatically. One-off service changes announced by the council (for example severe weather disruptions) are not reflected.
