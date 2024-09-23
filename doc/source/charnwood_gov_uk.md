# Charnwood

Support for schedules provided by [Charnwood](https://www.charnwood.gov.uk/), serving Charnwood, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: charnwood_gov_uk
      args:
        address: ADDRESS
        
```

### Configuration Variables

**address**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: charnwood_gov_uk
      args:
        address: 111, Main Street, Swithland
        
```

## How to get the source argument

Find the parameter of your address using [https://my.charnwood.gov.uk/](https://my.charnwood.gov.uk/) and write them exactly like on the web page.
