# Wollongong City Council

Support for schedules provided by [Wollongong City Council](https://wollongongwaste.com).

Source script for wollongongwaste.com.au

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wollongongwaste_com_au
      args:
        propertyID: PROPERTYID
```

### Configuration Variables

**propertyID**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: wollongongwaste_com_au
      args:
        propertyID: '21444'
```

## How to get the source arguments

Open the Waste Calendar at https://www.wollongongwaste.com.au/calendar/ with your browser's developer tools on the Network tab and look up your address. The last request is for '<propertyID>.json', e.g. https://wollongong.waste-info.com.au/api/v1/properties/21444.json
