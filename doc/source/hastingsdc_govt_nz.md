# Hastings District Council, NZ

[Source URL](https://www.hastingsdc.govt.nz/services/rubbish-and-recycling/collection-days/)

[API URL](https://data.napier.govt.nz/hdc/ncc/widgets/collectiondays/do_collectiondays.php)

This source provides waste collection schedules for Hastings District Council. It uses Napier Council's API's to fetch waste collection schedules based on the provided address.

## Configuration via `configuration.yaml`

To configure the source, add the following to your `configuration.yaml` file:

```yaml
waste_collection_schedule:
  sources:
    - name: hastings_govt_nz
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
    - name: hastingsdc_govt_nz
      args:
        address: 200 Heretaunga Street East
```
