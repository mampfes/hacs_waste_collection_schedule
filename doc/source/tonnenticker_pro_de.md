# Tonnenticker Pro

Support for waste collection schedules provided by [Tonnenticker Pro](https://www.regioit.de) (RegioIT), serving municipalities in Kreis Warendorf and parts of Kreis Gütersloh, Germany.

## Supported Municipalities

Ahlen, Beckum, Beelen, Borgholzhausen, Drensteinfurt, Ennigerloh, Everswinkel, Gütersloh, Halle (Westf), Harsewinkel, Herzebrock-Clarholz, Langenberg, Oelde, Ostbevern, Rheda-Wiedenbrück, Rietberg, Sassenberg, Schloß Holte-Stukenbrock, Sendenhorst, Steinhagen, Telgte, Versmold, Wadersloh, Warendorf, Werther (Westf)

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: tonnenticker_pro_de
      args:
        city: CITY_NAME
        street: STREET_NAME
```

### Configuration Variables

**city**
*(string) (required)*
Municipality name — use exact spelling from the list above.

**street**
*(string) (required)*
Street name — use the exact spelling shown in the Tonnenticker Pro app or the provider's website. Some streets include a section in brackets (e.g. `Waldbadstraße (Bahnhofstr. bis Rote Erde)`).

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: tonnenticker_pro_de
      args:
        city: Steinhagen
        street: "Waldbadstraße (Bahnhofstr. bis Rote Erde)"
```
