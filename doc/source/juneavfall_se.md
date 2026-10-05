# Jönköping - June Avfall & Miljö

Support for schedules provided by [Jönköping - June Avfall & Miljö](https://www.juneavfall.se).

Source for June Avfall & Miljö waste collection.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: juneavfall_se
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
    - name: juneavfall_se
      args:
        street_address: Storgatan 12, Huskvarna
```

## How to get the source arguments

Enter your street address as the provider's own address search lists it, including the locality.
