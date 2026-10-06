# Cairns Regional Council

Support for schedules provided by [Cairns Regional Council](https://www.cairns.qld.gov.au).

Source for Cairns Regional Council, QLD, Australia.

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

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cairns_qld_gov_au
      args:
        address: 7 Keats Close, MOUNT SHERIDAN
```

## How to get the source arguments

Go to the Cairns Regional Council [Find my bin day](https://www.cairns.qld.gov.au/water-waste-roads/waste-and-recycling/bin-collection/find-bin-day) page, start typing your address and pick it from the autocomplete list. Use the same 'STREET NUMBER STREET NAME, SUBURB' format shown in the suggestion for the `address` argument.
