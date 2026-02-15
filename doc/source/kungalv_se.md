# Kungälvs kommun avfallshantering

Support for schedules provided by [Kungälvs kommun](https://www.kungalv.se/Bygga--bo--miljo/avfall-och-atervinning/avfall-fran-hushall/), serving the municipality of Kungälv, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: kungalv_se
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**
*(string) (required)* : Street address including the city where the waste is picked up.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kungalv_se
      args:
        street_address: Dämmevägen 11, Kungälv
```

## How to get the source argument

The source argument is the street address of the property with waste collection. You can verify your address works by checking the [Kungälv customer portal](https://minasidor-va-avfall.kungalv.se/FutureWeb) or using the Kungälv Avfall app.
