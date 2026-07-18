# Jumomind

Support for schedules provided by [Jumomind](https://www.jumomind.de).

Source for Jumomind.de waste collection.

## Configuration via configuration.yaml

### Using city

```yaml
waste_collection_schedule:
  sources:
    - name: jumomind_de
      args:
        service_id: SERVICE_ID
        street: STREET
        house_number: HOUSE_NUMBER
        city: CITY
```

### Using city_id and area_id

```yaml
waste_collection_schedule:
  sources:
    - name: jumomind_de
      args:
        service_id: SERVICE_ID
        street: STREET
        house_number: HOUSE_NUMBER
        city_id: CITY_ID
        area_id: AREA_ID
```

### Configuration Variables

**service_id**  
*(string) (required)*

**city**  
*(string) (alternative)*

**city_id**  
*(string) (alternative)*

**area_id**  
*(string) (alternative)*

**street**  
*(string) (optional)*

**house_number**  
*(string) (optional)*

Provide one of: `city` or `city_id` + `area_id`.

## Example

### Using city

```yaml
waste_collection_schedule:
  sources:
    - name: jumomind_de
      args:
        service_id: sbm
        street: "Mei\xDFener Str."
        house_number: 6A
        city: Minden
```

## How to get the source arguments

Pick the 'service_id' for your region from the source's list of municipalities, then enter your town ('city') and where required the street ('street') and house number ('house_number'). Alternatively provide a known 'city_id' and 'area_id' directly.
