# Landkreis Northeim (unofficial)

Support for schedules provided by [Landkreis Northeim (unofficial)](https://abfall.nerdbridge.de/).

Unofficial waste collection schedule for Landkreis Northeim via abfall.nerdbridge.de.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nerdbridge_de
      args:
        municipality: MUNICIPALITY
```

### Configuration Variables

**municipality**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: nerdbridge_de
      args:
        municipality: Einbeck (Bezirk 2)
```

## How to get the source arguments

Go to https://abfall.nerdbridge.de/ and select your municipality. Use the displayed municipality name.
