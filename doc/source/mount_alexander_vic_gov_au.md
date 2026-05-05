# Mount Alexander Shire Council

Support for waste collection schedules provided by [Mount Alexander Shire Council](https://www.mountalexander.vic.gov.au), VIC, Australia.

## Configuration

```yaml
waste_collection_schedule:
  sources:
    - name: mount_alexander_vic_gov_au
      args:
        address: "1 Mostyn Street Castlemaine Victoria 3450"
```

### Arguments

| Argument | Type | Required | Description |
|---|---|---|---|
| `address` | string | Yes | Full street address, e.g. `1 Mostyn Street Castlemaine Victoria 3450` |
