# Abfall Kreis Steinburg

Support for schedules provided by [abfall.steinburg.de](https://abfall.steinburg.de).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_steinburg_de
      args:
        city: CITY without zip code
        street: STREET
        street_number: STREET_NUMBER
```

### Configuration Variables

**city**  
*(string) (required)* : The city name without zip code

**street**  
*(string) (required)* : The street name

**street_number**  
*(string) (optional)* : The street number

## Examples

### Example 1
```yaml
waste_collection_schedule:
  sources:
    - name: abfall_steinburg_de
      args:
        city: "Wacken"
        street: "Hauptstr."
        street_number: "1"
```
### Example 2
```yaml
waste_collection_schedule:
  sources:
    - name: abfall_steinburg_de
      args:
        city: "Vaale"
        street: "Bollweg"
```

## How to get the source arguments
You can find the possible values for `city` and `street` by using the search form on the [abfall.steinburg.de](https://abfall.steinburg.de) website.
