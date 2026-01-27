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

This source uses the AWIDO system. To find the correct spelling for your street and to check if a house number is required, follow these steps:

1.  Open the [official Waste App Ebersberg (Web Version)](https://ebe.app.awido.de/home).
2.  Start typing your **city** (Ort) and select it from the list.
3.  If a **street selection** (Straße) appears after selecting the city, it means the schedule varies by street. Note the exact spelling from the dropdown list.
4.  If a **house number selection** (Hausnummer) appears after selecting the street, it means you must also provide the `housenumber` argument.

### Tips for spelling:
- The integration is generally case-insensitive.
- If you enter an incorrect street name, the integration will list all available streets for that city in the Home Assistant log.
- Typical abbreviations like "Str." for "Straße" should be copied exactly as they appear in the official app.
