# GLØR

Support for schedules provided by [GLØR](https://glor.no).

Source for GLØR (Gudbrandsdal Lillehammer Øyer Ringebu Renovasjon), Norway.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: glor_no
      args:
        address: ADDRESS
```

### Configuration Variables

**address**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: glor_no
      args:
        address: Storgata 1, Lillehammer
```

## How to get the source arguments

Search for your address at glor.no/tømmeplan. Use the address exactly as shown in the result list, optionally followed by the municipality name, for example 'Storgata 1, Lillehammer'.
