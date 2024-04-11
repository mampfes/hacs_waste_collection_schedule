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

**address**  
*(string) (optional)*

**entry_id**
*(string) (optional)*

Either address or entry_id is required. (Providing both will ignore the address.)

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: wastenet_org_nz
      args:
        address: "31 Conyers Street"
```

```yaml
waste_collection_schedule:
  sources:
    - name: wastenet_org_nz
      args:
        entry_id: "23571"
```

## How to get the source argument

- The source argument is simply the full house mailing address as displayed in the web form.
- The entry_id is the unique identifier for the address. It is part of the URL when you search for your address on the WasteNet website. For example, if the URL is `https://www.wastenet.org.nz/bin-day/?entry_id=23571`, then the entry_id is `23571`.

