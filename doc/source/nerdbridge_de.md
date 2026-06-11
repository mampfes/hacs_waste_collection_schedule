# Landkreis Northeim (unofficial)

This source retrieves waste collection schedules for Landkreis Northeim, Germany, from the unofficial community service at [abfall.nerdbridge.de](https://abfall.nerdbridge.de/).

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

Name of your municipality, exactly as shown on [abfall.nerdbridge.de](https://abfall.nerdbridge.de/). For example: `Einbeck (Bezirk 2)`, `Bad Gandersheim`, `Northeim (Bezirk 1)`.

## How to get the configuration arguments

1. Go to [https://abfall.nerdbridge.de/](https://abfall.nerdbridge.de/).
2. Select your municipality from the drop-down list.
3. Copy the municipality name exactly as it appears in the list and use it as the `municipality` parameter.

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: nerdbridge_de
      args:
        municipality: Einbeck (Bezirk 2)
```

```yaml
waste_collection_schedule:
  sources:
    - name: nerdbridge_de
      args:
        municipality: Bad Gandersheim
```

```yaml
waste_collection_schedule:
  sources:
    - name: nerdbridge_de
      args:
        municipality: Northeim (Bezirk 1)
```
