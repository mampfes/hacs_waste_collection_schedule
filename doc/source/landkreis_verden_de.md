# Landkreis Verden

Support for schedules provided by [Landkreis Verden](https://landkreis-verden.de/), Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_verden_de
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

**house_number_addition**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_verden_de
      args:
        city: Achim
        street: Am Schießstand
        house_number: 10
```

```yaml
waste_collection_schedule:
  sources:
    - name: landkreis_verden_de
      args:
        city: Blender
        street: Buchenweg
        house_number: 8
        house_number_addition: a
```

## How to get the source arguments

Go to <https://lkv.landkreis-verden.de/WasteManagementVerden/WasteManagementServlet>, to get the correct values for the three address arguments.
