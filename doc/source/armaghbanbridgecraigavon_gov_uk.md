# Armagh City Banbridge & Craigavon

Support for schedules provided by [Armagh City Banbridge & Craigavon](https://www.armaghbanbridgecraigavon.gov.uk), serving Armagh City Banbridge & Craigavon, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: armaghbanbridgecraigavon_gov_uk
      args:
        address_id: ADDRESS ID
        
```

### Configuration Variables

**address_id**  
*(Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: armaghbanbridgecraigavon_gov_uk
      args:
        address_id: 185622007
```

## How to get the source argument

Find the parameter of your address using [https://www.armaghbanbridgecraigavon.gov.uk/resident/when-is-my-bin-day/](https://www.armaghbanbridgecraigavon.gov.uk/resident/when-is-my-bin-day/) after selecting your address. The address ID is the number at the end of the URL after `address=`.
