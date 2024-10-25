# EKM Mittelsachsen GmbH

EKM Mittelsachsen GmbH is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Go to <https://www.ekm-mittelsachsen.de/service-dienstleistungen/entsorgungstermine-abfallkalender>
- Select a year and your location.
- Right-click on `Digitalen Kalender exportieren` to copy the link.
- Replace the `url` in the example configuration with this link.
- Replace the year in the pasted link by {%Y}

## Examples

### Flöha, OT Falkenau

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://www.ekm-mittelsachsen.de/service-dienstleistungen/entsorgungstermine-abfallkalender?tx_ekmabfallkalender_abfallkalender%5Baction%5D=getIcal&tx_ekmabfallkalender_abfallkalender%5Bcity_id%5D=9886&tx_ekmabfallkalender_abfallkalender%5Bdistrict_id%5D=6871&tx_ekmabfallkalender_abfallkalender%5Byear%5D={%Y}&cHash=fcebd5160307e9c5690f3c7e02dcd869&tx_ekmabfallkalender_abfallkalender[types][]=r&tx_ekmabfallkalender_abfallkalender[types][]=p&tx_ekmabfallkalender_abfallkalender[types][]=l&tx_ekmabfallkalender_abfallkalender[trigger_days]=0
```
