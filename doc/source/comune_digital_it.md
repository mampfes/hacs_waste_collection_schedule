# Comune.Digital

Support for schedules provided by [Comune.Digital](https://comune.digital).

Source for Italian municipalities using the Comune.Digital (GoodBarber) app platform.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: comune_digital_it
      args:
        city: CITY
```

### Configuration Variables

**city**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: comune_digital_it
      args:
        city: santostefanodicamastra
```

## How to get the source arguments

The city identifier is the subdomain of your municipality's Comune.Digital website. For example, if the website is https://santostefanodicamastra.comune.digital, the city identifier is "santostefanodicamastra".
