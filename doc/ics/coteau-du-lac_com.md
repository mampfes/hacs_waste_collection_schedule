# Coteau-du-Lac, Québec

Coteau-du-Lac, Québec is supported by the generic [ICS](/doc/source/ics.md) source. For all available configuration options, please refer to the source description.


## How to get the configuration arguments

- Visit <https://portail.coteau-du-lac.com/calendrier-de-collectes> (the portal is in French only).
- Enter your address under "Pour quelle adresse désirez-vous obtenir le calendrier?", pick it from the
  suggestions and press "Soumettre".
- Under "Ajouter à mon calendrier", right-click the Apple calendar icon and select `Copy link address`.
- Use this copied URL as the `url` parameter. The `webcal://` prefix is handled automatically.

## Examples

### Coteau-du-Lac

```yaml
waste_collection_schedule:
  sources:
    - name: ics
      args:
        url: https://portail.coteau-du-lac.com/avis/collectes/v2/calendrier.ics?collects=4,5
```
