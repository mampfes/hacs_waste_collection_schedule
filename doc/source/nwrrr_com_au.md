# North West Resource Recovery and Recycling

Support for schedules provided by [North West Resource Recovery and Recycling](https://www.nwrrr.com.au).

Source for North West Resource Recovery and Recycling (NWRRR), serving 8 councils in north-west Tasmania, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nwrrr_com_au
      args:
        municipality: MUNICIPALITY
        region: REGION
```

### Configuration Variables

**municipality**  
*(string) (required)*

**region**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: nwrrr_com_au
      args:
        municipality: Devonport
        region: Devonport (Thursday)
```

## How to get the source arguments

Visit https://www.nwrrr.com.au/map, click 'Select Location', then choose your council and region from the list. Use the displayed council name as 'municipality' and the region name as 'region'.
