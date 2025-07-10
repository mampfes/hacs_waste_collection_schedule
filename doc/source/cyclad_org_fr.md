# Cyclad

Support for schedules provided by [Cyclad](https://cyclad.org/) in Charente-Maritime, France.

The list of available communes can be retrieved from `https://cyclad.org/wp-json/vernalis/v1/communes`.
Use the `ID` value of your commune as the `city_id` parameter.

Example for Nancras (`ID` 254):

```yaml
waste_collection_schedule:
  sources:
    - name: cyclad_org_fr
      args:
        city_id: 254
```
