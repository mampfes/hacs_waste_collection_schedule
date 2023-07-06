# Armadale (Western Australia)

Support for schedules provided by [Armadale (Western Australia)](https://www.armadale.wa.gov.au), serving Armadale (Western Australia), Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: armadale_wa_gov_au
      args:
        address: ADDRESS
        
```

### Configuration Variables

**address**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: armadale_wa_gov_au
      args:
        address: 23 Sexty St, ARMADALE
        
```

## How to get the source argument

Find the parameter of your address using [https://www.armadale.wa.gov.au/my-waste-collection](https://www.armadale.wa.gov.au/my-waste-collection) and write them exactly like on the web page.
