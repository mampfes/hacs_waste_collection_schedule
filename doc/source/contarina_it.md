# Contarina

Support for schedules provided by [Contarina.it](https://contarina.it/).

## Types

Supported waste types for this sources are:
- Secco
- Carta
- VPL (vetro, plastica e lattine)
- Umido
- Vegetale

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: contarina_it
      args:
        district: DISTRICT_NAME
```

### Configuration Variables

**district_name**  
*(string) (required)* 

The list of allowed district names (comune) can be found in the [calendar page](https://contarina.it/cittadino/raccolta-differenziata/eco-calendario).

## Example

```yaml
waste_collection_schedule:
  sources:
   - name: contarina_it
      args:
        district: Treviso
```
