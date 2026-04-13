**Configuration via configuration.yaml**

```yaml
waste_collection_schedule:
  sources:
    - name: enfield_gov_uk
      args:
        address: 127 Palmerston Rd, London N22 8QX
```

You can also configure the source directly with a UPRN:

```yaml
waste_collection_schedule:
  sources:
    - name: enfield_gov_uk
      args:
        uprn: "207102166"
```

**Configuration Variables**

**address** _(string)_: Full Enfield address as used on the council site. This is the easiest option if you do not know your UPRN.

**uprn** _(string)_: Unique Property Reference Number for your property. Use this if address matching is ambiguous.

How to find your UPRN:

1. Search for your property on the Enfield Council collection-day page: <https://www.enfield.gov.uk/services/rubbish-and-recycling/find-my-collection-day>
2. If you still need the UPRN directly, use <https://www.findmyaddress.co.uk/>

Example:

```yaml
waste_collection_schedule:
  sources:
    - name: enfield_gov_uk
      args:
        address: 127 Palmerston Rd, London N22 8QX
```
