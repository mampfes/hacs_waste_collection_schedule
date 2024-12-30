# Conwy County Borough Council

Support for schedules provided by [Conwy County Borough Council](https://www.conwy.gov.uk/), serving Conwy, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: conwy_gov_uk
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
    - name: conwy_gov_uk
      args:
        uprn: "200003177805"
        
```

## How to get the source argument

Go to <https://www.conwy.gov.uk/en/Resident/Recycling-and-Waste/Check-my-collection-day.aspx>, enter your postcode and click 'Submit'. In the list of addresses that appears, right click your address and select 'Copy Link' or 'Copy Link Address'. Paste this URL somewhere - the last element of this URL is your UPRN: https://www.conwy.gov.uk/Contensis-Forms/erf/collection-result-soap-xmas2025.asp?ilangid=1&uprn={UPRN}

Another way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
