# Wollondilly Shire Council

Support for schedules provided by [Wollondilly Shire Council](https://www.wollondilly.nsw.gov.au/), serving Wollondilly Shire Council, Australia.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: wollondilly_nsw_gov_au
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
    - name: wollondilly_nsw_gov_au
      args:
        address: 87 Remembrance Driveway TAHMOOR NSW
        
```

## How to get the source argument

Find the parameter of your address using [https://www.wollondilly.nsw.gov.au/waste-services/lookup-your-clean-up-details](https://www.wollondilly.nsw.gov.au/waste-services/lookup-your-clean-up-details) and write them exactly like on the web page.
