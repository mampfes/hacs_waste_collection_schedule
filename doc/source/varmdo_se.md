# Värmdö Sophämtning

Support for schedules provided by [Värmdö kommun](https://www.varmdo.se/), serving Värmdö, Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: varmdo_se
      args:
        street_address: STREET_ADDRESS
```

### Configuration Variables

**street_address**  
*(String) (required)* Your street name as shown on the Värmdö waste collection page.

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: varmdo_se
      args:
        street_address: "Rosenmalmsvägen"
```

## How to get the source arguments

Visit the [Värmdö hämtveckor](https://www.varmdo.se/byggabomiljo/avfallochatervinning/alltomavfallochatervinning/avfallshamtning/hamtveckoravfallfastlandet.4.4fd26e29194d31bcc1fa6ed.html) page and find your street name in the table.
