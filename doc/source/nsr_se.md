# NSR - Nordvästra Skånes Renhållnings AB

Support for schedules provided by [NSR - Nordvästra Skånes Renhållnings AB](https://nsr.se).

Source for NSR waste collection schedule in northwest Skåne, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: nsr_se
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: nsr_se
      args:
        address: "Signestorpsv\xE4gen 1"
```

## How to get the source arguments

Enter your street address as shown on the NSR website (e.g. 'Storgatan 1'). Do not include postal code. Search at https://nsr.se/privat/allt-om-din-sophamtning/nar-toms-mitt-karl/tomningskalender/
