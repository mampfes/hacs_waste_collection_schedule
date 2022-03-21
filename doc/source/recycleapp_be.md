# Recycle!

Support for schedules provided by [Recycle / recycleapp.be](https://www.recycleapp.be/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: recycleapp_be
      args:
        postcode: POST_CODE
        street: STREET
        house_number: HOUSE_NUMBER
        add_events: ADD_EVENTS
```

The source arguments are simply the values of the form elements on the homepage.

### Configuration Variables

**postcode**<br>
*(int)*
Postal Code.

**street**<br>
*(string)*
Street name.

**house_number**<br>
*(int)*
House number

**add_events**<br>
*(boolean)*
Add events (e.g. Repair Cafe) in addition to waste collections.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: recycleapp_be
      args:
        postcode: 1140
        street: Bazellaan
        house_number: 1
```
