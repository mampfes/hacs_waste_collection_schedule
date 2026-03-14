# Hushållsavfall och matavfall Värmdö

This is a waste collection schedule integration for Värmdö kommun in Sweden.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: varmdo_se
      args:
        address: ADDRESS
```

### Configuration Variables

**address**
*(string) (required)*

## Examples

```yaml
waste_collection_schedule:
  sources:
    - name: varmdo_se
      args:
        address: Abborrberget
```

## How to get the correct address

Visit [Hämtveckor avfall fastlandet](https://www.varmdo.se/byggabomiljo/avfallochatervinning/alltomavfallochatervinning/avfallshamtning/hamtveckoravfallfastlandet.4.4fd26e29194d31bcc1fa6ed.html) look for address.