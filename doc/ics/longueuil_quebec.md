# Longueuil (QC)

Longueuil (QC) is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- If you don't know your sector, go to `https://longueuil.quebec/fr/collectes` and use the "Outil interactif - Collectes" (enter your address or postal code) to identify your sector.
- Once you know your sector number, scroll to and expand the section titled "Calendrier des collectes XXXX : secteurs 1 à 10" (replace XXXX with the year).
- Scroll down to the "Versions virtuelles" subsection.
- Right-click on your sector and select `Copy link`.
- Use this copied URL as the `url` parameter.

## Examples

### Secteur 3

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        regex: Collecte\s*\|\s*(.*)
        url: https://cms.longueuil.quebec/sites/default/files/medias/documents/2025-11/2025-11/calendrier%202026%20secteur%203.ics
```
