# Abfallwirtschaft Wiener Neustadt

Support for schedules provided by [abfall.wiener-neustadt.at](https://abfall.wiener-neustadt.at/) for the city of Wiener Neustadt, Austria.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_wiener_neustadt_at
      args:
        street: STREET_NAME
        # Optional parameters (defaults shown):
        # rm_art: "monatlich"
        # restmuell: true
        # biotonne: true
        # wertstoffe: true
        # altkleider: true
        # christbaum: true
```

### Configuration Variables

**street**  
*(string) (required)*

Street name in Wiener Neustadt. Must match exactly as it appears on the website.

---

**str_id**  
*(string) (optional)*

Street ID. If provided, the street name lookup will be skipped. Can be used if you know the exact street ID from the website.

---

**rm_art**  
*(string) (optional, default: `"monatlich"`)*

Collection frequency for residual waste (Restmüll):
- `"wöchentlich"` or `"weekly"` or `"31"` = weekly collection
- `"14-tägig"` or `"2weeks"` or `"bi-weekly"` or `"33"` = bi-weekly collection
- `"monatlich"` or `"monthly"` or `"36"` = monthly collection

Note: This parameter controls the frequency but does not disable Restmüll collection. To exclude Restmüll dates, set `restmuell: false`.

---

**restmuell**  
*(boolean) (optional, default: `true`)*

Include residual waste (Restmüll) collection dates. The collection frequency is controlled by the `rm_art` parameter.

---

**biotonne**  
*(boolean) (optional, default: `true`)*

Include organic waste (Biotonne) collection dates.

---

**wertstoffe**  
*(boolean) (optional, default: `true`)*

Include recyclables (Wertstoffe / Yellow Bag) collection dates.

---

**altkleider**  
*(boolean) (optional, default: `true`)*

Include textile (Altkleider) collection dates.

---

**christbaum**  
*(boolean) (optional, default: `true`)*

Include Christmas tree collection dates (typically in January).

---

## Examples

### Minimal Configuration - All Waste Types with Defaults

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_wiener_neustadt_at
      args:
        street: "Leithakoloniestraße"
```
This will fetch all waste types with monthly Restmüll collection (default settings).

### Weekly Restmüll Collection

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_wiener_neustadt_at
      args:
        street: "Hauptplatz"
        rm_art: "wöchentlich"
```

### Only Biotonne (Organic Waste)

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_wiener_neustadt_at
      args:
        street: "Martinsgasse"
        restmuell: false
        wertstoffe: false
        altkleider: false
        christbaum: false
```

### Monthly Restmüll without Biotonne

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_wiener_neustadt_at
      args:
        street: "Martinsgasse"
        biotonne: false
        wertstoffe: false
```

### Monthly Collection

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_wiener_neustadt_at
      args:
        street: "Martinsgasse"
        rm_art: "monatlich"
        biotonne: false
        wertstoffe: false
```

### Only Residual Waste and Organic Waste

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_wiener_neustadt_at
      args:
        street: "Bahngasse"
        rm_art: "wöchentlich"
        biotonne: true
        wertstoffe: false
        altkleider: false
```

### Using Street ID (Advanced)

If you know the street ID, you can specify it directly to skip the street lookup:

```yaml
waste_collection_schedule:
  sources:
    - name: abfall_wiener_neustadt_at
      args:
        street: "Martinsgasse"
        str_id: "12345"
        rm_art: "monatlich"
```

## How to Find Your Street

Visit [https://abfall.wiener-neustadt.at](https://abfall.wiener-neustadt.at) and select your street from the dropdown menu. The street name must match exactly as shown in the dropdown.

## Supported Waste Types

- **Restmüll** - Residual Waste
- **Biotonne** - Organic Waste
- **Wertstoffe** - Recyclables / Yellow Bag
- **Altpapier** - Paper
- **Altkleider** - Textiles
- **Christbaum** - Christmas Tree (seasonal)

## Notes

- The integration automatically fetches the current year's collection schedule
- Past collection dates are filtered out automatically
- The collection frequency (`rm_art`) only affects residual waste; other waste types have their own fixed schedules
- Special collection dates (like Christmas trees) are typically only available in January
