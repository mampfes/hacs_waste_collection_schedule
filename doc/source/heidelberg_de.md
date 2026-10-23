# Heidelberg

Support for schedules provided by [Heidelberg](https://www.heidelberg.de/abfall).

Support for the waste collection schedule provided by the Office of Waste Management and Municipal Cleansing Heidelberg

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: heidelberg_de
      args:
        street: STREET
        collect_residual_waste_weekly: COLLECT_RESIDUAL_WASTE_WEEKLY
        even_house_number: EVEN_HOUSE_NUMBER
```

### Configuration Variables

**street**  
*(string) (required)*

**collect_residual_waste_weekly**  
*(string) (optional)*

**even_house_number**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: heidelberg_de
      args:
        street: "Alte Bergheimer Stra\xDFe"
```

## How to get the source arguments

Enter your street exactly as listed on heidelberg.de/abfall. Where the street allows a fortnightly residual waste round, switch off `collect_residual_waste_weekly` and state whether your house number is even.
