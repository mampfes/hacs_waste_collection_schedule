# Heinz-Entsorgung (Landkreis Freising)

Support for schedules provided by [Heinz-Entsorgung](https://abfallkalender.heinz-entsorgung.de/), Landkreis Freising, Germany.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: heinz_entsorgung_de
      args:
        param: PARAM
```

### Configuration Variables

**param**  
*(string) (required)*

The encrypted parameter for your location and street. See instructions below on how to obtain this.

## How to get the source arguments

**Note:** The website has changed and now uses a client-side API with encrypted parameters. You need to extract the parameter from the website using browser Developer Tools.

### Step-by-Step Instructions:

1. Open <https://abfallkalender.heinz-entsorgung.de/> in your web browser
2. Open the browser's Developer Tools:
   - **Chrome/Edge**: Press `F12` or right-click and select "Inspect"
   - **Firefox**: Press `F12` or right-click and select "Inspect Element"
   - **Safari**: Enable Developer menu in Settings, then select "Develop" → "Show Web Inspector"
3. Go to the **Network** tab in the Developer Tools
4. On the website:
   - Select your **location** (Ort) from the first dropdown
   - Then select your **street** (Straße) from the second dropdown
5. Watch the Network tab for a request to:
   ```
   api-enttermine.heinz-entsorgung.net/termine
   ```
6. Click on that network request
7. Look at the **Query String Parameters** section or the full **Request URL**
8. Find and copy the value of the `param` parameter
   - It will be a long Base64-encoded string (e.g., `yesJWYk53alJXaiMiOMJWYk53alJXagMnRlJXapNmbicCLvJnciQiOBJGblxncoNXYzVWZi4CLzJHdhJ3clNjIioWTv93c0Nici4CLqJWYyhjIiojMyASN9J`)
9. Use this value as the `param` argument in your Home Assistant configuration

### Visual Guide:

When you open the Developer Tools and select your address on the website, you should see something like:

```
Request URL: https://api-enttermine.heinz-entsorgung.net/termine?param=yesJWYk53alJXaiMiOMJWYk53alJXagMnRlJXapNmbicCLvJnciQiOBJGblxncoNXYzVWZi4CLzJHdhJ3clNjIioWTv93c0Nici4CLqJWYyhjIiojMyASN9J
```

Copy everything after `param=` (the long encoded string).

**Important Notes:**
- The parameter is encrypted and unique to your specific location and street combination
- You cannot manually create or modify this parameter
- Each address requires its own parameter extracted from the website
- The parameter should remain valid for an extended period (typically until the next calendar year)
- If you receive errors, try extracting a new parameter from the website

## Example

```yaml
waste_collection_schedule:
  sources:
    - name: heinz_entsorgung_de
      args:
        param: yesJWYk53alJXaiMiOMJWYk53alJXagMnRlJXapNmbicCLvJnciQiOBJGblxncoNXYzVWZi4CLzJHdhJ3clNjIioWTv93c0Nici4CLqJWYyhjIiojMyASN9J
```

## Waste Types

The source automatically detects waste types returned by the API. Common waste types include:

- **Restabfall** - Residual waste
- **Gelber Sack** - Yellow bag (plastic/packaging)
- **Bioabfall / BIO** - Organic waste
- **Papier** - Paper
- **Problemmüll** - Hazardous waste
- **Sperrmüll** - Bulky waste

Additional information (like container sizes) may be included in parentheses.

## Troubleshooting

### HTTP Error 400: Query Params Error

This error indicates that the `param` value is invalid or has expired. Please extract a fresh parameter from the website following the instructions above.

### No waste collection dates returned

Make sure you have selected both **Ort** (location) and **Straße** (street) on the website before copying the parameter. The API only returns dates when a complete address is configured.
