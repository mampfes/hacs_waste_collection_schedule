# iTouchVision Source using the encrypted API

Support for schedules provided by [iTouchVision Source using the encrypted API](https://www.itouchvision.com/), serving various council areas across the UK.

## Local Government Reorganisation note
Several of the areas served by this source are either currently or will soon be affected by Local Government Reorganisation (LGR) in England. Please continue to use the existing source for your local area for as long as it is still working. New sources for newly-created local authorities in England are not expected to be live until April 2028 or April 2029 at the earliest, when the new councils for those areas officially come into being.

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

- AYLESBURY VALE
- BLAENAU GWENT
- BUCKINGHAMSHIRE
- CHILTERN
- EPSOM AND EWELL
- HYNDBURN
- MENDIP
- NEWPORT
- SEDGEMOOR
- SOMERSET
- SOMERSET COUNTY
- SOMERSET WEST AND TAUNTON
- SOUTH SOMERSET
- TEST VALLEY
- WINCHESTER

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
