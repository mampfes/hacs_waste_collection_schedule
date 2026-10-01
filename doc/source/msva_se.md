# Mittsverige Vatten & Avfall

Support for schedules provided by [Mittsverige Vatten & Avfall](https://www.msva.se).

Source for Mittsverige Vatten & Avfall (MSVA) waste collection schedule, Sundsvall kommun.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: msva_se
      args:
        street: STREET
        house_number: HOUSE_NUMBER
        postal_code: POSTAL_CODE
        city: CITY
        additional_information: ADDITIONAL_INFORMATION
```

### Configuration Variables

**street**  
*(string) (required)*

**house_number**  
*(string) (required)*

**postal_code**  
*(string) (required)*

**city**  
*(string) (optional)*

**additional_information**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: msva_se
      args:
        street: "V\xE4stra Radiogatan"
        house_number: '18'
        postal_code: '85461'
        city: Sundsvall
```

## How to get the source arguments

Enter the full street address for a property in Sundsvall kommun. The API only supports Sundsvall (municipality code 2281); Timrå and Nordanstig addresses are not covered. Use the same street, house number, postal code and city you would enter on msva.se. Additional information is a house letter or unit identifier, e.g. 'A'; leave it empty if not applicable.
