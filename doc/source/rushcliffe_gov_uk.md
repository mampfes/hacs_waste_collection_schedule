# Rushcliffe Brough Council

Support for schedules provided by [Rushcliffe Brough Council](https://www.rushcliffe.gov.uk/), serving Rushcliffe Brough Council, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: rushcliffe_gov_uk
      args:
        postcode: POSTCODE
        address: ADDRESS
        
```

### Configuration Variables

**postcode**  
*(String) (required)*

**address**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: rushcliffe_gov_uk
      args:
        postcode: NG12 5FE
        address: 2 Church Drive, Keyworth, NOTTINGHAM, NG12 5FE
        
```

## How to get the source argument

Find the parameter of your address using [https://selfservice.rushcliffe.gov.uk/renderform.aspx?t=1242&k=86BDCD8DE8D868B9E23D10842A7A4FE0F1023CCA](https://selfservice.rushcliffe.gov.uk/renderform.aspx?t=1242&k=86BDCD8DE8D868B9E23D10842A7A4FE0F1023CCA) and write them exactly like on the web page.
