# Orange County, FL

Support for schedules provided by [Orange County, FL](https://ocarcims.ocfl.net/).

Source for Orange County Government curbside collection schedules.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: ocarcims_ocfl_net
      args:
        parcel_id: PARCEL_ID
```

### Configuration Variables

**parcel_id**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: ocarcims_ocfl_net
      args:
        parcel_id: 012128690001243
```

## How to get the source arguments

Search for your address at https://ocarcims.ocfl.net/ or https://www.ocpafl.org/. The 15-digit parcel ID appears in the search results on either site.
