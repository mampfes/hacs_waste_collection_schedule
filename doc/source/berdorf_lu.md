# Gemeng Bäertref (Berdorf, Luxembourg)

Support for schedules provided by [berdorf.lu](https://www.berdorf.lu/service-citoyens/dechets).

Covers the villages of Bäertref (Berdorf), Bollendorferbréck (Bollendorf-Brück), Wellerbaach (Weilerbach), Grondhaff (Grundhof), and Kalkesbaach (Kalkesbach).

The source fetches the current year's *Offallkalenner* PDF from the commune website and parses it automatically. No configuration arguments are required.

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
  sources:
    - name: berdorf_lu
```

## Collected waste types

| Type | Description |
|------|-------------|
| Hausmüll | Residual waste (every Friday except public holidays) |
| Biotonne | Kitchen/bio waste (same day as Hausmüll) |
| Glas | Glass (every 2nd Tuesday) |
| Papier | Paper (every 2nd Tuesday, same day as Glas) |
| PMC | Plastic, metal and carton packaging (every 2nd Wednesday) |
| Organische und inerte Abfälle | Organic and inert waste (Mondays, April–October) |
| Sperrmüll | Bulky waste (specific dates, see PDF) |
| SuperDrecksKëscht | Hazardous household waste collection (4× per year) |
| Altkleidersammlung | Clothes collection (specific dates) |
