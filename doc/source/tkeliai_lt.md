# Telšių keliai

Support for schedules provided by [Telšių keliai](https://tkeliai.lt).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tkeliai_lt
      args:
        location: LOCATION
```

### Configuration Variables

**location**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: tkeliai_lt
      args:
        location: Butkų Juzės(1-31) g.
```

## How to get the source arguments

Visit the [Atliekų išvežimo grafikas](https://tkeliai.lt/kalendorius/) page and search for your address.