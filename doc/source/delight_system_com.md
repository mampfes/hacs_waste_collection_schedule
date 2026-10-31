# ThreeR

Support for schedules provided by [ThreeR](https://threer1.delight-system.com).

Source for Japanese municipalities using the ThreeR garbage collection app.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: delight_system_com
      args:
        language_code: LANGUAGE_CODE
        municipality: MUNICIPALITY
        area_name: AREA_NAME
```

### Configuration Variables

**language_code**  
*(string) (required)*

**municipality**  
*(string) (required)*

**area_name**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: delight_system_com
      args:
        municipality: shinjukuku
        area_name: Aizumi-cho
        language_code: en
```

## How to get the source arguments

Enter your municipality and neighbourhood exactly as shown in the ThreeR garbage app (e.g. municipality `Shinjuku City`, area `Aizumi-cho`). Where the app asks for several levels, enter all of them, separated by ` / ` (e.g. `Okubo / 1 chome`). If a value is not recognised, the setup form will offer matching options from the live API.
