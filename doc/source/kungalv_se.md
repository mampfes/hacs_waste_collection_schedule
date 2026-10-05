# Kungälvs kommun Avfallshantering

Support for schedules provided by [Kungälvs kommun Avfallshantering](https://www.kungalv.se/Bygga--bo--miljo/avfall-och-atervinning/avfall-fran-hushall/).

Source script for kungalv.se

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
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: kungalv_se
      args:
        street_address: "Komministergatan 4, Kung\xE4lv"
```

## How to get the source arguments

Enter your street address as the provider's own address search lists it, including the locality.
