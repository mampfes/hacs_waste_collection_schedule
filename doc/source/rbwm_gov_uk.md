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

Go to [https://forms.rbwm.gov.uk/bincollections](https://forms.rbwm.gov.uk/bincollections) and search for your address. When you see your upcoming collections your address bar should look something like this: `https://forms.rbwm.gov.uk/bincollections?uprn=100080381393`. The value after `uprn=` is your UPRN (`100080381393` in this example)

Another way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
