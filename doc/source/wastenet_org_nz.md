# Gore, Invercargill & Southland

Support for schedules provided by [Gore, Invercargill & Southland](https://www.wastenet.org.nz).

Source for Wastenet.org.nz.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: wastenet_org_nz
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
    - name: wastenet_org_nz
      args:
        address: 166 Lewis Street, Invercargill
```

## How to get the source arguments

Visit https://www.wastenet.org.nz and find your property address. Use the full address, e.g. '166 Lewis Street, Invercargill' or '1 Anderson Place, Gore'. Since the v3 pipeline migration, waste types use canonical, localised names; update filters, automations and customisations using the old labels.
