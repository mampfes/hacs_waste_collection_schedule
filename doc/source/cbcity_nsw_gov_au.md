# City of Canterbury-Bankstown (NSW)

Support for schedules provided by [City of Canterbury-Bankstown](https://bindayfinder.azurewebsites.net/), serving Canterbury-Bankstown, NSW, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cbcity_nsw_gov_au
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(String) (required)* Full street address including suburb and postcode, e.g. "102 Crinan Street, Hurlstone Park 2193"

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cbcity_nsw_gov_au
      args:
        address: "102 Crinan Street, Hurlstone Park 2193"
```

## How to get the source arguments

Visit the [Canterbury-Bankstown Bin Day Finder](https://bindayfinder.azurewebsites.net/) and enter your address. Use the full address as shown in the results including suburb and postcode.
