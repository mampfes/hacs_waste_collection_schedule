# GLØR

Support for schedules provided by [GLØR](https://glor.no) (Gudbrandsdal Lillehammer Øyer Ringebu Renovasjon), serving the municipalities of Lillehammer, Øyer, Ringebu and Gausdal, Norway.

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
*(String) (required)*

The address, optionally followed by the municipality name after a comma, for example `Storgata 1, Lillehammer`. The municipality is only required if the same street name exists in more than one municipality served by GLØR.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: glor_no
      args:
        address: Storgata 1, Lillehammer
```

## How to get the source argument

Visit [https://glor.no/tømmeplan](https://glor.no/t%C3%B8mmeplan), search for your address, and use the address exactly as shown in the result list, optionally followed by the municipality name.
