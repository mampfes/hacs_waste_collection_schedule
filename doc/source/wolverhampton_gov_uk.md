# Wolverhampton City Council

```yaml
waste_collection_schedule:
  sources:
    - name: wolverhampton_gov_uk
      args:
        postcode: "WV1 1RD"
        uprn: "10094887108"
```

Enter your `postcode` and `uprn` from the council's In Your Area property page. Both argument names remain unchanged.

The source follows the council's View the calendar link, discovers its current Drupal calendar route and reads explicitly dated service rows. It preserves the printed year at month boundaries and seasonal gaps. Only services actually listed for the property are returned; communal properties may not list individual general-waste/recycling collections. The public garden schedule does not confirm a subscription.

The former HTML-card selectors returned no entries after the site changed. No fixed recurrence or inferred holiday dates are added. Types now use canonical, localised names; update filters and customisations using old labels.
