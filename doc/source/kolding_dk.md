# Kolding Kommune

Support for schedules provided by [Kolding Kommune](https://kolding.dk/), serving Kolding municipality, Denmark.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kolding_dk
      args:
        id: See description
```

### Configuration Variables

**id**  
_(String) (required)_

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kolding_dk
      args:
        id: "00007b8d-0002-0001-4164-647265737320"
```

## How to get the id

1. Go to https://kolding.infovision.dk/public/selectaddress
2. Search for your address.
3. Your ID is in the resulting URL, e.g. `https://kolding.infovision.dk/public/address/00007b8d-0002-0001-4164-647265737320`
4. The ID is the UUID at the end: `00007b8d-0002-0001-4164-647265737320`
