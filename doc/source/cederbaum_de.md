# Cederbaum Braunschweig

Support for schedules provided by [Cederbaum Braunschweig](https://www.cederbaum.de).

Cederbaum Braunschweig Paperimüll

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cederbaum_de
      args:
        street: STREET
```

### Configuration Variables

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cederbaum_de
      args:
        street: Hans-Sommer-Str.
```

## How to get the source arguments

Enter your street exactly as it is listed on https://www.cederbaum.de/blaue-tonne/ (e.g. 'Adolfstr. 31-42').
