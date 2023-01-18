# Bürgerportal

Source for waste collection in multiple service areas.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: buergerportal_de
      args:
        operator: OPERATOR
        district: DISTRICT
        subdistrict: SUBDISTRICT
        street: STREET_NAME
        number: HOUSE_NUMBER
        show_volume: SHOW_VOLUME
```

## Supported Operators

- `alb_donau`: <https://buerger-portal-albdonaukreisabfallwirtschaft.azurewebsites.net>
- `biedenkopf`: <https://biedenkopfmzv.buergerportal.digital>
- `cochem_zell`: <https://buerger-portal-cochemzell.azurewebsites.net>

### Configuration Variables

**operator**\
_(string) (required)_

**district**\
_(string) (required)_

**street**\
_(string) (required)_

**number**\
_(string|int) (required)_

**subdistrict**\
_(string) (optional) (default: null)_

**show_volume**\
_(boolean) (optional) (default: false)_

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: buergerportal_de
      args:
        operator: cochem_zell
        district: Bullay
        subdistrict: Bullay
        street: Layenweg
        number: 3
```

## How to get the source arguments

1. Open the URL of your operator and click on the menu option `Abfuhrkalender` in the left sidebar.
2. Select your `district` (Ort). _Note_: If your district contains two values separated by a comma, you also have to specify the `subdistrict` (Ortsteil): Enter the first part into the field `district` and the second part into the field `subdistrict`. This is necessary even if your `district` and `subdistrict` have the same value (e.g., `Bullay, Bullay`). Subdistrict may only be left empty if there is no comma in the field value.
3. Select your `street` (Straße).
4. Select your `number` (Hausnummer).

All parameters are _case-sensitive_.

## Notes on Container Volumes

By default, this sources does not differentiate between different container sizes.
If your operator collects large containers (1000 l) on different dates than smaller ones (e.g., 120 l or 240 l), you may set `show_volume: true` in your configuration.
If you do, the volume will be added to the waste type.
For example, the collection `Bio` with a volume of 120 l would then be shown as `Bio (120 l)`.
With this additional information, you can adjust all waste collections to your needs by making use of a source's [`customize` option](../installation.md#configuring-sources).
