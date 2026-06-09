# Stadtgemeinde Klosterneuburg

Support for schedules provided by [Stadtgemeinde Klosterneuburg](https://www.klosterneuburg.at/Natur_Umwelt/Recycling/Muellabfuhr/Muellabfuhrkalender), Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: klosterneuburg_at
      args:
        street: STREET
        house_number: HOUSE_NUMBER
```

### Configuration Variables

**street**
*(string) (required)*

**house_number**
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: klosterneuburg_at
      args:
        street: "Kierlinger Straße"
        house_number: "10"
```

## How to get the source arguments

Go to the [Klosterneuburg Müllabfuhrkalender](https://www.klosterneuburg.at/Natur_Umwelt/Recycling/Muellabfuhr/Muellabfuhrkalender) and use the street and house number exactly as shown in the dropdown.
