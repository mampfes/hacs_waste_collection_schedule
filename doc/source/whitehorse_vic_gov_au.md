# Whitehorse City Counfil

Support for schedules provided by [Whitehorse City Counfil](https://www.whitehorse.vic.gov.au), serving Whitehorse, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: whitehorse_vic_gov_au
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
    - name: whitehorse_vic_gov_au
      args:
        address: 17 Main Street BLACKBURN
        
```

## How to get the source argument

Find the parameter of your address using [https://map.whitehorse.vic.gov.au/index.html?entity=lyr_waste](https://map.whitehorse.vic.gov.au/index.html?entity=lyr_waste) and write them exactly like on the web page.
