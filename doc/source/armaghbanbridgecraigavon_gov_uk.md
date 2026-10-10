# Armagh City Banbridge & Craigavon

Support for schedules provided by [Armagh City Banbridge & Craigavon](https://www.armaghbanbridgecraigavon.gov.uk).

Source for Armagh City Banbridge & Craigavon.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: armaghbanbridgecraigavon_gov_uk
      args:
        address_id: ADDRESS_ID
```

### Configuration Variables

**address_id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: armaghbanbridgecraigavon_gov_uk
      args:
        address_id: 185622007
```

## How to get the source arguments

Find the parameter of your address using https://www.armaghbanbridgecraigavon.gov.uk/resident/when-is-my-bin-day/, after selecting your address. The address ID is the number at the end of the URL after `address=`.
