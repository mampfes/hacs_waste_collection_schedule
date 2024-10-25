# Solihull

Waste collection schedules provided by [Solihull](https://www.solihull.gov.uk/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: solihull_gov_uk
      args:
        uprn: UPNR
        predict: PREDICT
```

### Configuration Variables

**uprn**  
*(string|integer) (required)*

**predict**  
*(bool) (optional, default=False)*  
*predict the next 10 weeks of collection dates based on the next collection date and the frequency of collections (only returns the next collection date if set to False)*

## Example

### Example 1

```yaml
waste_collection_schedule:
  sources:
    - name: solihull_gov_uk
      args:
        uprn: 100070994046
```

### Example with prediction

```yaml
waste_collection_schedule:
  sources:
    - name: solihull_gov_uk
      args:
        uprn: 200003821723
        predict: True
```


## How to get your UPRN

You can see the uprn in the address bar after searching your address in the [Solihull Council Bincollection Form](https://digital.solihull.gov.uk/BinCollectionCalendar/).

another easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
