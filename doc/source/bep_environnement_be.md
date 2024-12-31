# BEP Environnement

Support for schedules provided by [bep-environnement.be](https://www.bep-environnement.be/).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: bep_environnement_be
      args:
        locality: LOCALITY
```

The arguments can be found in the URL after visiting the [the calendar](https://www.bep-environnement.be/). Type your *Postal Code* or *City Name* then select the **Locality**. This is the value you have to give in argument.

### Configuration Variables

**locality**
*(string)*
Name of your Locality (Localité).

## Example

```yaml
# URL: https://www.bep-environnement.be/

waste_collection_schedule:
  sources:
    - name: bep_environnement_be
      args:
        locality: "Dinant"
```
