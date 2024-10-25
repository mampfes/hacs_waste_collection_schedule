# Napier City Council

[Source URL](https://www.napier.govt.nz/services/rubbish-and-recycling/collection-days/)

[API URL](https://data.napier.govt.nz/regional/ncc/widgets/collectiondays/do_collectiondays.php)

This source provides waste collection schedules for Napier City Council. It uses the Napier Council's API's to fetch waste collection schedules based on the provided address.

## Configuration via `configuration.yaml`

To configure the source, add the following to your `configuration.yaml` file:

```yaml
waste_collection_schedule:
  sources:
    - name: napier_govt_nz
      args:
        address: UNIQUE_ADDRESS
```

## Configuration Variables

**address** (string) (required)  
The address for which you want to retrieve the waste collection schedule.

## Example

An example configuration:

```yaml
waste_collection_schedule:
  sources:
    - name: napier_govt_nz
      args:
        address: 4 Sheehan Street
```
