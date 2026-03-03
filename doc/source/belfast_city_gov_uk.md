# Belfast City Council Waste Collection Schedule

This is a custom provider for the [HACS Waste Collection Schedule](https://github.com/mampfes/hacs_waste_collection_schedule) integration.

## Installation

1. Copy `belfast_city_gov_uk.py` to your `custom_components/waste_collection_schedule/waste_collection_schedule/source/` directory
2. Restart Home Assistant
3. Configure the integration

## Configuration

### Option 1: Simple (using postcode only)

If you only provide a postcode, the integration will automatically use the **first address** found at that postcode.

```yaml
waste_collection_schedule:
  sources:
    - name: belfast_city_gov_uk
      args:
        postcode: "BT1 5GS"
```

### Option 2: Specific Address (using UPRN)

If multiple properties share a postcode, you can specify the exact property using its UPRN (Unique Property Reference Number).

```yaml
waste_collection_schedule:
  sources:
    - name: belfast_city_gov_uk
      args:
        postcode: "BT1 5GS"
        uprn: "123456789"
```

## How to Find Your UPRN

1. Open your browser's Developer Tools (F12)
2. Go to the Network tab
3. Visit https://online.belfastcity.gov.uk/find-bin-collection-day/Default.aspx
4. Enter your postcode and click Search
5. Look at the address dropdown - each address has a UPRN value
6. Inspect the dropdown HTML or check the Network POST request payload to find your UPRN

Alternatively:
1. Enter your postcode on the Belfast City Council website
2. Right-click on the address dropdown and select "Inspect Element"
3. Find the `<option>` tag for your address
4. The `value` attribute is your UPRN

Example:
```html
<option value="123456789">BELFAST CITY HALL, BELFAST, BT1 5GS</option>
```
The UPRN is `123456789`.

## Supported Bin Types

- **Recycling bin** (Blue bin) - 🔵
- **Compost bin** (Brown bin) - 🟤
- **General waste bin** (Black bin) - ⚫

## Example Sensor Configuration

```yaml
sensor:
  - platform: waste_collection_schedule
    name: Belfast Recycling Bin
    source_index: 0
    details_format: "next_3_items"
    value_template: '{{ value.types|join(", ") }}'
    types:
      - Recycling bin

  - platform: waste_collection_schedule
    name: Belfast Compost Bin
    source_index: 0
    details_format: "next_3_items"
    value_template: '{{ value.types|join(", ") }}'
    types:
      - Compost bin

  - platform: waste_collection_schedule
    name: Belfast General Waste
    source_index: 0
    details_format: "next_3_items"
    value_template: '{{ value.types|join(", ") }}'
    types:
      - General waste bin
```

## How It Works

This provider scrapes the Belfast City Council waste collection website using a two-step process:

1. **Step 1**: Submit your postcode to get a list of addresses
   - The website returns addresses with their UPRNs
   - If no UPRN is provided, it uses the first address

2. **Step 2**: Submit the selected address (UPRN) to get bin collection dates
   - The website returns a table with bin types and collection dates

The provider handles all the ASP.NET WebForm complexity (`__VIEWSTATE`, `__EVENTVALIDATION`, etc.) automatically.

## Troubleshooting

**"No addresses found for postcode"**
- Check your postcode is correct and includes a space (e.g., "BT1 5GS" not "BT15GS")
- Verify the postcode is within Belfast City Council area

**Wrong address being used**
- Provide the UPRN parameter to specify the exact property

**Collection dates not updating**
- The integration fetches data according to your scan_interval setting
- Try restarting Home Assistant or updating manually

## Support

For issues with this provider, please check:
1. That your postcode is valid and in the Belfast City Council area
2. The Belfast City Council website is accessible: https://online.belfastcity.gov.uk/find-bin-collection-day/
3. Your Home Assistant logs for error messages

## Credits

- Created for use with [HACS Waste Collection Schedule](https://github.com/mampfes/hacs_waste_collection_schedule)
- Data source: [Belfast City Council](https://www.belfastcity.gov.uk/)
