# Coburg Entsorgungs- und Baubetrieb CEB

Support for schedules provided by [Coburg Entsorgungs- und Baubetrieb CEB](https://www.ceb-coburg.de/), serving City of Coburg, Germany.

Landkreis Coburg is not supported by this source but by the [awido_de source](/doc/source/awido_de.md).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: ceb_coburg_de
      args:
        street: STREET NAME
```

### Configuration Variables

**street**  
*(String) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: ceb_coburg_de
      args:
        street: Kanalstraße, Seite HUK
```

## How to get the source argument

You can validate your parameter by looking for your street here: <https://abfuhrkalender.ceb-coburg.de/>
