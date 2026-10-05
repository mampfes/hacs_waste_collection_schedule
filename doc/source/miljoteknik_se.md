# Ronneby Miljöteknik

Support for schedules provided by [Ronneby Miljöteknik](http://www.fyrfackronneby.se).

Source for Ronneby Miljöteknik waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: miljoteknik_se
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: miljoteknik_se
      args:
        street_address: "Hjortsbergav\xE4gen 16, Johannishus"
```

## How to get the source arguments

Enter your street address and city separated by a comma, as they appear when you search for your address on http://www.fyrfackronneby.se/hamtningskalender/, e.g. 'Hjortsbergavägen 16, Johannishus'.
