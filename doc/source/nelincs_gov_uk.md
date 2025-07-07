# North East Lincolnshire Council

Support for schedules provided by [North East Lincolnshire Council](https://www.nelincs.gov.uk/), serving North East Lincolnshire Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: nelincs_gov_uk
      args:
        uprn: "UPRN"
        
```

### Configuration Variables

**uprn**  
*(String | Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: nelincs_gov_uk
      args:
        uprn: "11042949"
        
```

## How to get the source argument

Fill in your address details at [North East Lincolnshire Council's Find My Address](https://www.nelincs.gov.uk/find-my-address/), the Unique Property Reference Number (UPRN) will be shown in the URL field when you see your collection schedule. (e.g. `https://www.nelincs.gov.uk/?s=DN40+1JU&uprn=11043243` where `11043243` is the UPRN).

Another easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
