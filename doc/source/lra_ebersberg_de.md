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
- Zorneding (including Pöring and Wolfesing)

## How to get the configuration arguments

This source uses the AWIDO system. Requirements for street and house number vary by municipality:

1.  **Uniform Schedule**: In some municipalities (e.g., Zorneding), the schedule is the same for the entire town. You only need to provide the `city`.
2.  **Street-dependent**: In larger towns (e.g., Poing), you must provide the `street`.
3.  **House-number-dependent**: In some cases (e.g., parts of Vaterstetten), even the `housenumber` is required.

Check the **official "Abfall-App Ebersberg"** on your smartphone to see which level of detail is required for your address.

### Tips for spelling:
- The integration is generally case-insensitive.
- If you enter an incorrect street name, the integration will list all available streets for that city in the Home Assistant log.
