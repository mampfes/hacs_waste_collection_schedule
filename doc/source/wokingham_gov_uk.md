# Wokingham Borough Council

Support for schedules provided by [Wokingham Borough Council](https://www.wokingham.gov.uk/rubbish-and-recycling/find-your-bin-collection-day"), serving Wokingham, UK.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: wokingham_gov_uk
      args:
        postcode: POSTCODE
        property: PROPERTY_REFERENCE_NUMBER
```

### Configuration Variables
**postcode**  
*(string) (required)*

**property**  
*(string) (required)*

## Example

```yaml
waste_collection_schedule:
    sources:
    - name: wokingham_gov_uk
      args:
        postcode: "RG40 1GE"
        property: "56199"
```

## How to find your Property Reference Number
You can find you Property Reference Number by running the [wokingham_uk](/custom_components/waste_collection_schedule/waste_collection_schedule/wizard/wokingham_uk.py) wizard script. For a given postcode, it will list addresses and associated Property Reference Number. For example:

```bash
Enter your postcode: RG40 1GE
56164 = 2 Samborne Drive Wokingham
56165 = 4 Samborne Drive Wokingham
56166 = 6 Samborne Drive Wokingham
56167 = 8 Samborne Drive Wokingham
56168 = 10 Samborne Drive Wokingham
56169 = 12 Samborne Drive Wokingham
56170 = 14 Samborne Drive Wokingham
56171 = 16 Samborne Drive Wokingham
56172 = 18 Samborne Drive Wokingham
56173 = 20 Samborne Drive Wokingham
56174 = 22 Samborne Drive Wokingham
56175 = 24 Samborne Drive Wokingham
56176 = 26 Samborne Drive Wokingham
56177 = 28 Samborne Drive Wokingham
56178 = 30 Samborne Drive Wokingham
56190 = 32 Samborne Drive Wokingham
56191 = 34 Samborne Drive Wokingham
56192 = 36 Samborne Drive Wokingham
56193 = 38 Samborne Drive Wokingham
56194 = 40 Samborne Drive Wokingham
56195 = 42 Samborne Drive Wokingham
56196 = 44 Samborne Drive Wokingham
56197 = 46 Samborne Drive Wokingham
56198 = 48 Samborne Drive Wokingham
56199 = 50 Samborne Drive Wokingham
56200 = 52 Samborne Drive Wokingham
```

