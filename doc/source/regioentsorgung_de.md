# RegioEntsorgung

Support for schedules provided by [RegioEntsorgung](https://regioentsorgung.de/) located near Aachen, Germany.

This source only supports municipalities offered in the RegioEntsorgung address picker. Stadt Aachen itself is not part of that picker. For Stadt Aachen, use [abfallnavi_de](./abfallnavi_de.md) with `service: aachen`.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: regioentsorgung_de
      args:
          city: CITY
          street: STREET
          house_number: HOUSE_NUMBER
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**house_number**  
*(string | number) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: regioentsorgung_de
      args:
        city: Würselen
        street: Merzbrück
        house_number: 200
```

## How to get the source arguments

Go to <https://regioentsorgung.de/service/abholservice/abfallkalender>, to get the correct values for the three address arguments.

Street names from the provider may contain non-breaking spaces. The source normalizes whitespace during address matching, so entering regular spaces in Home Assistant works as expected.
