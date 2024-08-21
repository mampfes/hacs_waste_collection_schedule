# Itouchvision Source using the encrypted API

Support for schedules provided by [Itouchvision Source using the encrypted API](https://www.itouchvision.com/), serving multiple, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: iapp_itouchvision_com
      args:
        uprn: "UPRN"
        municipality: "MUNICIPALITY"
```

### Configuration Variables

**uprn**  
*(String | Integer) (required)*

**municipality**  
*(String) (required)*  
supported are:

- BUCKINGHAMSHIRE
- CHILTERN

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: iapp_itouchvision_com
      args:
        uprn: "100080550517"
        municipality: "BUCKINGHAMSHIRE"
        
```

## How to get the source argument

An easy way to discover your Unique Property Reference Number (UPRN) is by going to <https://www.findmyaddress.co.uk/> and entering in your address details.
