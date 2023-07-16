# Windsor and Maidenhead

Support for schedules provided by [Windsor and Maidenhead](https://my.rbwm.gov.uk/), serving Windsor and Maidenhead, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: rbwm_gov_uk
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
    - name: rbwm_gov_uk
      args:
        uprn: "100080381393"
        
```

## How to find your

Go to [https://my.rbwm.gov.uk/special/find-your-collection-dates](https://my.rbwm.gov.uk/special/find-your-collection-dates) and search for your address. When you see your upcoming collections your address bar should look something like this: `https://my.rbwm.gov.uk/special/your-collection-dates?uprn=100080381393&subdate=2023-07-16&addr=104%20St%20Andrews%20Crescent%20Windsor%20SL4%204EN`. The first argument (after `uprn=`) is your UPRN (`100080381393` in this example)

Another way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
