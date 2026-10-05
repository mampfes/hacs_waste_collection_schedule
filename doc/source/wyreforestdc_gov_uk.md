# Wyre Forest District Council

Support for schedules provided by [Wyre Forest District Council](https://www.wyreforestdc.gov.uk).

Source for wyreforestdc.gov.uk, Wyre Forest District Council, UK

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wyreforestdc_gov_uk
      args:
        street: STREET
        town: TOWN
        garden_cutomer: GARDEN_CUTOMER
```

### Configuration Variables

**street**  
*(string) (required)*

**town**  
*(string) (required)*

**garden_cutomer**  
*(string) (optional)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: wyreforestdc_gov_uk
      args:
        street: hilltop avenue
        town: BEWDLEY
        garden_cutomer: '308072'
```

## How to get the source arguments

Street and town must match the URL parameters you get when clicking an address at https://forms.wyreforestdc.gov.uk/querybin.asp. The garden waste customer number (garden_cutomer) is only needed for garden waste collections: go to https://forms.wyreforestdc.gov.uk/gardenwastechecker, enter your postcode and, before pressing Select on your address, open your browser's developer tools (F12) and its network tab. Pressing Select sends a POST request to https://forms.wyreforestdc.gov.uk/GardenWasteChecker/Home/Details; the customer number is the CUST_No value in its payload.
