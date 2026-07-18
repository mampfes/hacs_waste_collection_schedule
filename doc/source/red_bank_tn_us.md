# Red Bank, Tennessee

Support for schedules provided by [Red Bank, Tennessee](https://www.redbanktn.gov/257/Solid-Waste).

Source for residential trash collection in the City of Red Bank, TN.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: red_bank_tn_us
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
    - name: red_bank_tn_us
      args:
        street_address: 1107 Ashmore Ave
```

## How to get the source arguments

Enter your street address as it appears in Red Bank (e.g. '1107 Ashmore Ave'). The city/state/ZIP are optional. Your collection weekday is looked up from the city's official trash-day map.
