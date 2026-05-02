# Tunbridge Wells

Support for schedules provided by [Waltham Forest](https://www.walthamforest.gov.uk//), serving Waltham Forest, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: walthamforest_gov_uk
      args:
        uprn: UPRN
        
```

### Configuration Variables

**uprn**  
*(String | Integer) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: walthamforest_gov_uk
      args:
        uprn: 200001421821
        
```

## How to get the source argument

## Using findmyaddress.co.uk

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
