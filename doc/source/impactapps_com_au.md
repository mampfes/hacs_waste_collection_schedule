# Impact Apps

Support for schedules provided by [Impact Apps](https://impactapps.com.au).

Source for councils using Impact Apps (waste-info.com.au) for waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: impactapps_com_au
      args:
        service: SERVICE
        property_id: PROPERTY_ID
        suburb: SUBURB
        street_name: STREET_NAME
        street_number: STREET_NUMBER
```

### Configuration Variables

**service**  
*(string) (required)*

**property_id**  
*(string) (optional)*

**suburb**  
*(string) (optional)*

**street_name**  
*(string) (optional)*

**street_number**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: impactapps_com_au
      args:
        service: redland
        suburb: Redland Bay
        street_name: Boundary Street
        street_number: '1'
```

## How to get the source arguments

Service: the council's name as listed, its waste-info.com.au API URL (e.g. 'https://brisbane.waste-info.com.au'), or the first part of that host name (e.g. 'brisbane'). Then either the suburb, street name and street number, or the property ID, which the council's calendar page requests as '<property ID>.json' (browser developer tools, Network tab).
