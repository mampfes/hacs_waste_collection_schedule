# Gwynedd

Support for schedules provided by [Gwynedd](https://www.gwynedd.gov.uk/), serving Gwynedd, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: gwynedd_gov_uk
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
    - name: gwynedd_gov_uk
      args:
        uprn: "200003177805"
        
```

## How to get the source argument

Go to <https://diogel.gwynedd.llyw.cymru/Daearyddol/en/ChwilioCyfeiriad> and search for your address and select it. The last element of your URL is your UPRN: https://diogel.gwynedd.llyw.cymru/Daearyddol/en/LleDwinByw/Index/{UPRN}

Another way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
