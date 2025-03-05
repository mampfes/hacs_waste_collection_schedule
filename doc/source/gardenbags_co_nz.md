# GardenBags NZ

Support for schedules provided by [GardenBags NZ](https://gardenbags.co.nz/) and all their franchises (e.g [Auckland Garden Bag](https://www.aucklandgardenbagcompany.co.nz)).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: gardenbags_co_nz
      args:
        account_number: ACCOUNT NUMBER
        account_pin: ACCOUNT PIN
        franchise: FRANCHISE
        
```

### Configuration Variables

**account_number**
*(String) (required)*

**account_pin**
*(String) (required)*

**franchise**
*(String) (optional)*


## Example

```yaml
waste_collection_schedule:
    sources:
    - name: gardenbags_co_nz
      args:
        account_number: 123456
        account_pin: 1234
        franchise: AGB    
```

```yaml
waste_collection_schedule:
    sources:
    - name: gardenbags_co_nz
      args:
        account_number: 112233
        account_pin: 1122
```