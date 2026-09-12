# Mackay Regional Council

Support for schedules provided by [Mackay Regional Council](https://www.mackay.qld.gov.au/residents/services/waste), Queensland, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: mackay_qld_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

Your street address. The closest match returned by the council's address search is used, so the exact council formatting is not required.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: mackay_qld_gov_au
      args:
        address: 77 Wood Street Mackay
```

## How to get the source arguments

Visit the council's [Rubbish and bins](https://www.mackay.qld.gov.au/residents/services/waste) page and search for your address in the bin collection lookup. Any address string the search box resolves to your property will work — for example `77 Wood Street Mackay` or `115 Nebo Road West Mackay`.

The council publishes a weekly general waste collection and a fortnightly recycling collection.
