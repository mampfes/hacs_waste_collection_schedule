# Junker APP

Support for schedules provided by [Junker APP](https://junker.app), serving multiple municipalities in Italy.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: junker_app
      args:
        municipality: MUNICIPALITY (comune)
```

### Configuration Variables

**municipality**  
*(String) (required)*

**area**  
*(string) (optional)* Required by some municipalites

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: junker_app
      args:
        municipality: Val della torre
```

```yaml
waste_collection_schedule:
    sources:
    - name: junker_app
      args:
        municipality: Lodè
        area: Utenze non domestiche
```

## How to get the source argument

The parameter should match the suggested value from the website: <https://junker.app/cerca-il-tuo-comune/> page.
