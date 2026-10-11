# Nuneaton and Bedworth Borough Council

Support for schedules provided by [Nuneaton and Bedworth Borough Council](https://www.nuneatonandbedworth.gov.uk/).

Source for Nuneaton and Bedworth Borough Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nuneatonandbedworth_gov_uk
      args:
        street: STREET
```

### Configuration Variables

**street**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: nuneatonandbedworth_gov_uk
      args:
        street: Gloucester Close
```

## How to get the source arguments

Enter your street as the council's 'Find your bin collection day' directory lists it. Where a street name exists in both towns, add the town, e.g. 'Church Street, Bedworth'. Garden waste (green bin) dates only apply if you subscribe to the green bin service.
