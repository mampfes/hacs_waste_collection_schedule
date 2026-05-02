# Western Bay of Plenty District Council

Support for schedules provided by [Western Bay of Plenty District Council](https://www.westernbay.govt.nz/), serving the Western Bay of Plenty district in New Zealand via [kerbsidecollective.co.nz](https://kerbsidecollective.co.nz/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: western_bay_of_plenty_nz
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
    - name: western_bay_of_plenty_nz
      args:
        address: "15 Seaview Road"
```

## How to get the source argument

Visit [kerbsidecollective.co.nz](https://kerbsidecollective.co.nz/) and search for your address. Use the address string exactly as you would type it into the search box.
