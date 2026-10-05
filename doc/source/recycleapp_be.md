# Recycle!

Support for schedules provided by [Recycle!](https://www.recycleapp.be).

Source for RecycleApp.be

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: recycleapp_be
      args:
        street: STREET
        house_number: HOUSE_NUMBER
        postcode: POSTCODE
        add_events: ADD_EVENTS
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

**postcode**  
*(string) (required)*

**add_events**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: recycleapp_be
      args:
        postcode: 3001
        street: Waversebaan
        house_number: 276
```

## How to get the source arguments

Enter the postcode, street and house number as on https://www.recycleapp.be. Disable add_events to leave out events such as collection-point openings.
