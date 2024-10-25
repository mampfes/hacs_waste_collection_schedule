# Ittre

Support for schedules provided by [Ittre](https://www.ittre.be/), serving Ittre, Belgium.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: ittre_be        
```

NOTE: Some waste collection may not change for holidays as the site does not provide specific dates for all collection types (e.g. Organic waste : Every Monday - in case of public holiday: the previous Saturday) and we do not have a good way to get the respective holiday dates.
