# Sutton Council, London

Support for schedules provided by [Sutton Council, London](https://sutton.gov.uk), serving Sutton Council, London, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: sutton_gov_uk
      args:
        id: "ID"
        
```

### Configuration Variables

**id**  
*(String | Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: sutton_gov_uk
      args:
        id: "4721996"
        
```

## How to get the source argument

Goto [https://waste-services.sutton.gov.uk/waste](https://waste-services.sutton.gov.uk/waste) and select your location. Your address bar should show the internal ID of your address. Use this ID as the source argument. (e.g. `https://waste-services.sutton.gov.uk/waste/4721996` the ID is `4721996`)
