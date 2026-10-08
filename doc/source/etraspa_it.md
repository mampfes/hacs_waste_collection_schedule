# ETRA S.p.A.

Support for waste collection schedules published by [ETRA S.p.A.](https://www.etraspa.it/) for San Martino di Lupari, Italy.

The source downloads the current annual calendar from the municipality website. Select the zone shown on your ETRA calendar or in the ETRA app.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: etraspa_it
      args:
        zone: B
```

### Configuration variables

| Parameter | Type | Required | Description |
| --------- | ---- | -------- | ----------- |
| `zone` | string | Yes | Collection zone `A` or `B`, as shown on the ETRA calendar. |

## Returned collection types

- Secco residuo
- Plastica e metalli
- Carta e cartone
- Vetro
- Verde e ramaglie
- Umido organico
