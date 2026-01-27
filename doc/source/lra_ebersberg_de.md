# Landkreis Ebersberg

Landkreis Ebersberg is supported by the [AWIDO Online](/doc/source/awido_de.md) system. This source covers all 21 municipalities in the district.

## Configuration

```yaml
waste_collection_schedule:
  sources:
    - name: lra_ebersberg_de
      args:
        city: CITY
        street: STREET
        housenumber: HOUSENUMBER
```

### Configuration Variables

**city**
*(string) (required)*
The name of your municipality (e.g., Ebersberg, Poing, Vaterstetten, Zorneding).

**street**
*(string) (optional)*
Your street name. Required for some municipalities where schedules vary by street.

**housenumber**
*(string|integer) (optional)*
Your house number. Required if the schedule varies within a street.

## Supported Municipalities

- Anzing
- Aßling
- Baiern
- Bruck
- Ebersberg
- Egmating
- Emmering
- Forstinning
- Frauenneuharting
- Glonn
- Grafing
- Hohenlinden
- Kirchseeon
- Markt Schwaben
- Moosach
- Oberpframmern
- Pliening
- Poing
- Steinhöring
- Vaterstetten
- Zorneding

## How to get the configuration arguments

This source uses the AWIDO system. While many municipalities in Landkreis Ebersberg have a uniform schedule, some (like Poing or Vaterstetten) might require a street or house number.

You can verify the required parameters in the official "Abfall-App Ebersberg" or on the [Landratsamt Ebersberg website](https://www.lra-ebe.de/).
