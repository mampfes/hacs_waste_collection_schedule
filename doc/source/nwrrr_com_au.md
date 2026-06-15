# North West Resource Recovery and Recycling

Support for schedules provided by [North West Resource Recovery and Recycling](https://www.nwrrr.com.au), covering 8 councils in north-west Tasmania, Australia:

- Burnie
- Central Coast
- Circular Head
- Devonport
- Kentish
- Latrobe
- Waratah Wynyard
- West Coast

## Configuration via configuration.yaml

```yaml
waste_collection_schedule:
    sources:
    - name: nwrrr_com_au
      args:
        municipality: MUNICIPALITY
        region: REGION
```

### Configuration Variables

**municipality**
*(String) (required)*

The council name. One of: `Burnie`, `Central Coast`, `Circular Head`, `Devonport`, `Kentish`, `Latrobe`, `Waratah Wynyard`, `West Coast`.

**region**
*(String) (required)*

The region name within your council. See the table below or visit <https://www.nwrrr.com.au/map> to find your region.

## Examples

### Devonport (Thursday collection day)

```yaml
waste_collection_schedule:
    sources:
    - name: nwrrr_com_au
      args:
        municipality: Devonport
        region: "Devonport (Thursday)"
```

### Strahan (West Coast)

```yaml
waste_collection_schedule:
    sources:
    - name: nwrrr_com_au
      args:
        municipality: West Coast
        region: Strahan
```

## How to get the source arguments

1. Go to <https://www.nwrrr.com.au/map>.
2. Click **Select Location** in the side panel.
3. Choose your council from the dropdown.
4. Choose your region from the list.
5. Use the council name as `municipality` and the region name as `region`.

### Available regions by council

| Municipality | Regions |
|---|---|
| Burnie | Burnie (Monday), Burnie (Tuesday), Burnie (Wednesday), Burnie (Thursday) |
| Central Coast | East Ulverstone, Forth, Penguin, Penguin East, Sulphur Creek/Heybridge, Ulverstone, Ulverstone/Gawler, West Ulverstone (Thursday), West Ulverstone (Wednesday) |
| Circular Head | Rural A (Tuesday), Rural A (Wednesday), Rural B (Monday), Rural B (Tuesday), Rural B (Wednesday), Smithton East, Smithton North, Smithton South, Stanley |
| Devonport | Devonport (Friday), Devonport (Monday), Devonport (Thursday), Devonport (Tuesday), Devonport (Wednesday) |
| Kentish | Sheffield/Barrington, South Spreyton/Railton |
| Latrobe | Hawley/Shearwater, Latrobe North, Latrobe Rural, Latrobe South, Port Sorell |
| Waratah Wynyard | Lennah Drive, Little Village Lane, Sisters Beach/Boat Harbour, Somerset North, Somerset South, Waratah, Wynyard Central, Wynyard East, Wynyard West |
| West Coast | Gormanston, Queenstown, Rosebery, Strahan, Tullah, Zeehan |
