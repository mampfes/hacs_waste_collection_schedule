# De Afvalapp

De Afvalapp is a waste collection calendar platform used by several Dutch municipalities.
Supported municipalities include:

- Helmond
- Land van Cuijk
- Boekel
- Maashorst

## How to get the configuration arguments

- Visit <https://www.deafvalapp.nl> and enter your postcode and house number to make sure your address is recognized.
- Write down your postcode, house number and house number addition, if any (e.g. A).

### Configuration via yaml

```yaml
waste_collection_schedule:
  sources:
    - name: deafvalapp_nl
      args:
        postcode: YOUR_POSTCODE
        house_number: YOUR_HOUSE_NUMBER
        house_number_addition: YOUR_HOUSE_NUMBER_ADDITION
```

**Configuration Variables**

**postcode** _(string) (required)_: Dutch postal code of your address, e.g. `5406XP`

**house_number** _(string) (required)_: House number of your address, e.g. `9`

**house_number_addition** _(string)_: Optional house number addition, e.g. `A`

Example: Vluchtoord 9, 5406 XP Uden (Maashorst)

```yaml
waste_collection_schedule:
  sources:
    - name: deafvalapp_nl
      args:
        postcode: 5406XP
        house_number: 9
```
