# Central Otago District Council

Support for schedules provided by [Central Otago District Council](https://www.codc.govt.nz/) Rubbish & Recycling collection. It uses the endpoint of the [CODC Bin App](https://play.google.com/store/apps/details?id=nz.co.environz.codc) (built by Environz, the same backend used by Dunedin, Waitaki and Timaru's council bin apps).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: codc_govt_nz
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
    - name: codc_govt_nz
      args:
        address: "5 Campbell Street Alexandra"
```

## How to get the source argument

Use the [CODC Bin App](https://play.google.com/store/apps/details?id=nz.co.environz.codc) and search for your address. The `address` argument should match how the app displays your address alongside your next collection details.

---
