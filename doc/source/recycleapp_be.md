# Recycle!

Support for schedules provided by [Recycle / recycleapp.be](https://www.recycleapp.be/).

This source works for any Belgian municipality on the Fost Plus / RecycleApp.be platform — including local operators that present their own branded collection calendar on top of the same backend, e.g. [Ivago](https://www.ivago.be/) (Gent). If your local waste operator isn't listed by name anywhere in this repo, try this source with your postcode/street/house number before requesting a new one — it likely already works.

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

**postcode**  
*(int)*
Postal Code.

**street**  
*(string)*
Street name.

**house_number**  
*(int)*
House number

**add_events**  
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
