# Armadale (Western Australia)

Support for schedules provided by [Armadale (Western Australia)](https://my.armadale.wa.gov.au), serving Armadale (Western Australia), Australia.

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

Find the parameter of your address using [https://my.armadale.wa.gov.au/service/waste-and-recycling/find-your-bin-collection-day/](https://my.armadale.wa.gov.au/service/waste-and-recycling/find-your-bin-collection-day/) and write them exactly like on the web page.
