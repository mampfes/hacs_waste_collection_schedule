# WasteNet Southland

Support for schedules provided by [WasteNet Southland](http://wastenet.org.nz/), serving the Gore District Council, Invercargill City Council and Southland District Council.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wastenet_org_nz
      args:
        address: ADDRESS
```

### Configuration Variables

**address**<br>
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: wastenet_org_nz
      args:
        address: "67 Chesney Street"
```

## How to get the source argument

The source argument is simply the house mailing address as displayed in the web form.