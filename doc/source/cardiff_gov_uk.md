# Cambridge City Council

Support for schedules provided by [Cardiff Council](https://www.cardiff.gov.uk/ENG/resident/Rubbish-and-recycling/When-are-my-bins-collected/Pages/default.aspx), serving Cardiff (UK).

With many thanks to [Tom Brien](https://github.com/TomBrien) whose [existing work](https://github.com/TomBrien/cardiffwastepy) was used as the base for this.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: cardiff_gov_uk
      args:
        uprn: UPRN

```

### Configuration Variables

**UPRN**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: cardiff_gov_uk
      args:
        uprn: "100100124569"
```

## How to find your `UPRN`
An easy way to discover your Unique Property Reference Number (UPRN) is by going to https://www.findmyaddress.co.uk/ and entering in your address details.