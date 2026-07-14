# Cairns Regional Council

Support for schedules provided by [Cairns Regional Council](https://www.cairns.qld.gov.au/water-waste-roads/waste-and-recycling/bin-collection/find-bin-day), QLD, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cairns_qld_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

Full street address, e.g. `7 Keats Close, MOUNT SHERIDAN`. Use the same format shown in the address autocomplete on the council's website (street number and name, then a comma, then the suburb).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cairns_qld_gov_au
      args:
        address: "7 Keats Close, MOUNT SHERIDAN"
```

## How to get the source arguments

Visit the [Find my bin day](https://www.cairns.qld.gov.au/water-waste-roads/waste-and-recycling/bin-collection/find-bin-day) page, start typing your address, and pick it from the autocomplete list. Use the same `STREET NUMBER STREET NAME, SUBURB` format shown in the suggestion for the `address` argument.

## Notes

This source computes future collection dates from the council's next-collection API: general waste is collected weekly and recycling fortnightly, both anchored to the next occurrence returned by the council's website. Collection days may shift around public holidays; check the council's printable PDF calendar linked from the property page if you need to confirm a specific date.
