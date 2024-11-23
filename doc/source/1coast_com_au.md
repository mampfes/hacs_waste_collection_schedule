# 1Coast - Central Coast

Support for schedules provided by [1Coast - Central Coast](https://1coast.com.au/), serving Central Coast council, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: 1coast_com_au
      args:
        address: ADDRESS
        
```

### Configuration Variables

**address**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: 1coast_com_au
      args:
        address: 12 MAITLAND ST, NORAH HEAD. CENTRAL COAST 2263
        
```

## How to get the source argument

Visit <https://1coast.com.au/bin-collection/bin-collection-day/> and select your address. The address parameter should exactly match the address auto completed by the website.
