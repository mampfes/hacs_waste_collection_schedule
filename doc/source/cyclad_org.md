# Cyclad

Support for schedules provided by [Cyclad](https://cyclad.org/), France.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: cyclad_org
      args:
        commune: "Nancras"
        # or provide the ID directly
        # commune_id: 254
```

### Configuration Variables

**commune**
*(string) (optional)*
Name of the commune as listed on cyclad.org.

**commune_id**
*(integer) (optional)*
Identifier of the commune. If provided, name lookup is skipped.

At least one of `commune` or `commune_id` is required.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: cyclad_org
      args:
        commune: "Nancras"
```

## How to get the source arguments

Retrieve the list of available communes from `https://cyclad.org/wp-json/vernalis/v1/communes`.
Each item contains an `ID` and a `post_title`. Use the name with `commune` or the `ID` with `commune_id`.
