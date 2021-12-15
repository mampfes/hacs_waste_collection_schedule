# Stadtreinigung Hamburg

Add support for schedules provided by [stadtreinigung.hamburg](https://www.stadtreinigung.hamburg/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: stadtreinigung_hamburg
      args:
        hnId: HNID
```

### Configuration Variables

**hnId**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: stadtreinigung_hamburg
      args:
        hnId: 113084
```

## How to get the source arguments

Open [stadtreinigung.hamburg](https://www.stadtreinigung.hamburg/abfuhrkalender/) and search for schedules for your location.

Check the URL and extract the number after field `housenumber%5D`.

Example:

`https://www.stadtreinigung.hamburg/abfuhrkalender/?tx_srh_pickups%5Bstreet%5D=2586&tx_srh_pickups%5Bhousenumber%5D=53814`

The resulting `hnId` is `53814`.