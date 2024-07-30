# Porirua City

Support for schedules provided by [Porirua City](https://poriruacity.govt.nz/), serving Porirua City, Newzeeland.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: poriruacity_govt_nz
      args:
        address: ADDRESS
        
```

### Configuration Variables

**address**  
*(String) (required)*  
Should exactly match the address as shown in the web search result.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: poriruacity_govt_nz
      args:
        address: 6 Ration Lane, Whitby, Porirua City 5024
        
```

## How to get the source argument

Visit <https://poriruacity.govt.nz/services/rubbish-and-recycling/recycling-calendar/> and search for your location, then copy the exact address from the search result.
