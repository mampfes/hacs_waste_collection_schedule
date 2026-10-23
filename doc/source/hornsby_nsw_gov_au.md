# Hornsby Shire Council

Support for schedules provided by [Hornsby Shire Council](https://hornsby.nsw.gov.au/).

Source for Hornsby Shire Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hornsby_nsw_gov_au
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
    - name: hornsby_nsw_gov_au
      args:
        address: 1 Cherrybrook Road, West Pennant Hills, 2125
```

## How to get the source arguments

Search for your address on the Hornsby Shire Council website (Property > Waste and recycling) and enter it as it appears in the autocomplete result, e.g. `1 Cherrybrook Road, West Pennant Hills, 2125`.
