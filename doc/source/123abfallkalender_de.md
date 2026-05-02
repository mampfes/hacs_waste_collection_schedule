# 123abfallkalender

Support for waste collection schedules provided by [123abfallkalender.de](https://www.123abfallkalender.de/), serving Ebsdorfergrund municipality, Germany.

## Supported Districts

Beltershausen, Dreihausen, Ebsdorf, Frauenberg, Hachborn, Heskem, Ilschhausen, Leidenhofen, Mölln, Rauischholzhausen, Roßberg, Wermertshausen, Wittelsberg

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: 123abfallkalender_de
      args:
        district: DISTRICT_NAME
```

### Configuration Variables

**district**
*(string) (required)*
District name — use exact spelling from the list above.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: 123abfallkalender_de
      args:
        district: Beltershausen
```
