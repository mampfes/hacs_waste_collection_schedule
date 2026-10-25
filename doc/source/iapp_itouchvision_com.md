# iTouchVision Source using the encrypted API

Support for schedules provided by [iTouchVision Source using the encrypted API](https://www.itouchvision.com/).

Source for iTouchVision Source using the encrypted API.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: iapp_itouchvision_com
      args:
        uprn: UPRN
        municipality: MUNICIPALITY
```

### Configuration Variables

**uprn**  
*(string) (required)*

**municipality**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: iapp_itouchvision_com
      args:
        uprn: '10090955364'
        municipality: NEWPORT
```

## How to get the source arguments

Select your council, then enter the property UPRN. Buckinghamshire and Aylesbury Vale are read from the My Council Services portal. The former Chiltern source is this one with municipality BUCKINGHAMSHIRE.
