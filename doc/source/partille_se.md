# Partille kommun

Support for schedules provided by [Partille kommun](https://vatjanst.partille.se).

Source for Partille kommun waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: partille_se
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
    - name: partille_se
      args:
        street_address: "Tiondev\xE4gen 6, Partille"
```

## How to get the source arguments

Enter your street address as the provider's own address search lists it, including the locality.
