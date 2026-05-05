# Ville de Saguenay

Support for schedules provided by [Ville de Saguenay](https://ville.saguenay.ca).

## Configuration via GUI

1. Add "Waste Collection Schedule" integration
2. Select "Ville de Saguenay" as the source
3. Enter your building ID (`batiment` / `cle_batiment`)

## Configuration via YAML

```yaml
waste_collection_schedule:
  sources:
    - name: saguenay_ca
      args:
        batiment: 8773
```

### Configuration Variables

**batiment**  
*(Integer) (Required)*  
Building ID (`cle_batiment`) from the AJAX request payload. To find it:

1. Go to https://ville.saguenay.ca/services-aux-citoyens/environnement/horaire-des-collectes
2. Open your browser's developer tools (F12) and go to the **Network** tab
3. Enter your address in the search field
4. Look for a request named **collectesinfos** (full URL: `https://ville.saguenay.ca/ajax/collectes/collectesinfos`)
5. Click on it and go to the **Payload** tab
6. Copy the value of `cle_batiment`
7. Use this number as the `batiment` parameter

**Example:** If the payload shows `"cle_batiment": "8773"`, then use `batiment: 8773`

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: saguenay_ca
      args:
        batiment: 8773
```

## Waste Types

- Ordures (Trash) - `mdi:trash-can`
- Recyclage (Recycling) - `mdi:recycle`
- Compostage (Organic) - `mdi:leaf`
