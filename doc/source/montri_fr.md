# Montri

Support for schedules provided by [Montri](https://montri.fr), a French waste collection schedule platform used by several intercommunal waste-management syndicates, such as SICOVAD around Épinal (Vosges).

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: montri_fr
      args:
        postal_code: POSTAL_CODE
        city_name: CITY_NAME
        address: ADDRESS
```

### Configuration Variables

**postal_code**
*(String) (required)*

The postal code of your municipality, e.g. `88000`.

**city_name**
*(String) (required)*

The exact name of your municipality as shown on [https://montri.fr](https://montri.fr), e.g. `Dinozé`.

**address**
*(String) (required)*

The street address to search for (house number and street name), e.g. `6 Place Georges Boizot`.

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: montri_fr
      args:
        postal_code: "88000"
        city_name: Dinozé
        address: 6 Place Georges Boizot
```

## How to get the source arguments

Visit [https://montri.fr](https://montri.fr), enter your postal code and select your municipality from the dropdown. Then go to "Calendrier de collecte" and search for your address to confirm the exact spelling of your municipality and street address to use here.
