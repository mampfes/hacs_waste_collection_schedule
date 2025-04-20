# City of Greater Bendigo

Support for schedules provided by [City of Greater Bendigo](https://www.bendigo.vic.gov.au/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bendigo_vic_gov_au
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: bendigo_vic_gov_au
      args:
        street_address: 263-265 High Street Kangaroo Flat
```

## How to get the source arguments

Visit the [City of Greater Bendigo bin night](https://www.bendigo.vic.gov.au/residents/general-waste-recycling-and-organics/bin-night) page and search for your address. The ```street_address``` argument is input to the autocomplete for the bin night page so with whatever you enter, make sure it returns a unique result (best advice: street address + suburb). For unlisted addresses use an adjacent listed address.