# Hygea

Support for schedules provided by [hygea.be](https://www.hygea.be/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: hygea_id
      args:
        street_id: ID
```

You id can be found in the url when visiting the [the calendar](https://www.hygea.be/votre-calendrier-de-collecte.html) for your street.
It may also work by giving it your post code, but this "api" is a mess so only do that if you have no other choice

### Configuration Variables

**street_id**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: hygea_id
      args:
        street_id: 3758
```