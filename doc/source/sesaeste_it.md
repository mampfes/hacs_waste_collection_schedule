# S.E.S.A.

Support for schedules provided by [S.E.S.A.](https://sesaeste.it).

Source script for sesaeste.it

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: sesaeste_it
      args:
        user_municipality: USER_MUNICIPALITY
```

### Configuration Variables

**user_municipality**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: sesaeste_it
      args:
        user_municipality: Legnaro
```

## How to get the source arguments

Use the name of your municipality exactly as it appears in the municipality list of the S.E.S.A. app, for example `Legnaro`.
