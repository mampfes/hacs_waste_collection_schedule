# Czerwonak, Murowana Goślina, Oborniki

Support for schedules provided by [Czerwonak, Murowana Goślina, Oborniki](https://www.eko-tom.pl).

Source for eko-tom.pl. Municipalities: Czerwonak, Murowana Goślina, Oborniki

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: eko_tom_pl
      args:
        city: CITY
        street: STREET
        nr: NR
```

### Configuration Variables

**city**  
*(string) (required)*

**street**  
*(string) (required)*

**nr**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: eko_tom_pl
      args:
        city: Czerwonak
        street: "\u0179r\xF3dlana"
        nr: '39'
```
