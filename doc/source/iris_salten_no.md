# Iris Salten

Supported collection schedule for [Iris Salten](https://www.iris-salten.no/), covering Bodø and surrounding municipalities in Nordland, Norway.

The script uses the official Iris Salten API to dynamically look up your address and fetch the internal ID.

## Configuration via UI

1. Go to `Settings` -> `Devices & Services` -> `Add Integration`.
2. Search for `Waste Collection Schedule`.
3. Select `Iris Salten` from the list of providers.
4. Enter your street address and (optionally) your municipality.

## Configuration via `configuration.yaml`

### Configuration Variables

**address**
*(string) (required)*
Your street address exactly as it is written in the Iris Salten search field.

**kommune**
*(string) (optional)*
Your municipality (e.g., "Bodø kommune"). Providing this is recommended if your street name exists in multiple municipalities within the Iris Salten region.

### Basic Example

```yaml
waste_collection_schedule:
  sources:
    - name: iris_salten_no
      args:
        address: "Alsosgården 11"
        kommune: "Bodø kommune"
```
