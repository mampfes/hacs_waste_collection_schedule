# Calderdale Council

Support for schedules provided by [Calderdale Council](https://www.calderdale.gov.uk), UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: calderdale_gov_uk
      args:
        postcode: "OL14 7BX"
        uprn: "010010152783"
```

### Configuration Variables

**postcode**  
*(string) (required)*

**uprn**  
*(string | integer) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: calderdale_gov_uk
      args:
        postcode: "OL14 7BX"
        uprn: "010010152783"
```

## How to get the source arguments

### UPRN (Unique Property Reference Number)

To find your UPRN:

1. Visit the [Calderdale Council collection day finder](https://www.calderdale.gov.uk/environment/waste/household-collections/collectiondayfinder.jsp)
2. Enter your postcode and click "Find"
3. Select your address from the dropdown list
4. After submitting, check the URL in your browser - it will contain your UPRN
5. Alternatively, inspect the page source after selecting your address to find the UPRN value

Your UPRN will be a 12-digit number, typically starting with "0100".
