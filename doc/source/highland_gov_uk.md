# Highland

Support for schedules provided by [Highland](https://www.highland.gov.uk/), serving Highland, Scotland, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: highland_gov_uk
      args:
        uprn: UPRN
        predict: PREDICT_MULTIPLE_DATES
        
```

### Configuration Variables

**uprn**  
*(String | Integer) (required)*

**predict**  
*(Boolean) (optional|default=False)*  
Tries to predict the next collections based on the nextCollection date, and the frequency of the collection. Only returns one date per waste type if set to False. If set to True, it will try to predict the next 10 weeks of collections.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: highland_gov_uk
      args:
        uprn: 130108578
        # Implicit
        # predict: False
```

```yaml
waste_collection_schedule:
    sources:
    - name: highland_gov_uk
      args:
        uprn: 130007199
        predict: False  
```

```yaml
waste_collection_schedule:
    sources:
    - name: highland_gov_uk
      args:
        uprn: 130066519
        predict: True
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.

Or by going to uprn.uk and entering your postcode.
