# WasteNet Southland

Support for schedules provided by [WasteNet Southland](https://www.wastenet.org.nz/), serving the Gore District Council, Invercargill City Council and Southland District Council.

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

Your full street address including the city/town name, as it appears in the [WasteNet bin day finder](https://www.wastenet.org.nz/3-bin-day-finder).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: wastenet_org_nz
      args:
        address: "166 Lewis Street, Invercargill"
```

## How to get the source argument

1. Go to the [WasteNet bin day finder](https://www.wastenet.org.nz/3-bin-day-finder).
2. Start typing your street address in the search box and select the matching entry from the autocomplete dropdown.
3. Use the full address exactly as shown in the dropdown (e.g. `166 Lewis Street, Invercargill`).
