# De Afvalapp

Support for schedules provided by [De Afvalapp](https://www.deafvalapp.nl).

Source for De Afvalapp, used by several Dutch municipalities (e.g. Helmond, Land van Cuijk, Boekel, Maashorst).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: deafvalapp_nl
      args:
        postcode: POSTCODE
        house_number: HOUSE_NUMBER
        house_number_addition: HOUSE_NUMBER_ADDITION
```

### Configuration Variables

**postcode**  
*(string) (required)*

**house_number**  
*(string) (required)*

**house_number_addition**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: deafvalapp_nl
      args:
        postcode: 5406XP
        house_number: '9'
```

## How to get the source arguments

Enter the same postcode, house number and (optional) house number addition that you would use at https://www.deafvalapp.nl to look up your waste collection calendar.
