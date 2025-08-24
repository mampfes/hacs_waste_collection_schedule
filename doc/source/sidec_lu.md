# SIDEC

Support for SIDEC waste collections.

## Configuration

```yaml
waste_collection_schedule:
  sources:
    - name: sidec_lu
      args:
        commune_id: ID
```

### Arguments

**commune_id**  
*(string) (required)*

The ID of your municipality (`commune`).

### How to find the `commune_id`

1.  Go to the [SIDEC Calendar Page](https://www.sidec.lu/fr/Collectes/Calendrier).
2.  Open your browser's developer tools (usually by pressing F12).
3.  Select the 'Inspector' or 'Elements' tab.
4.  Find the `<select>` element with the `id="getcalendar"`.
5.  Look for your municipality in the list of `<option>` elements.
6.  The `commune_id` is the `value` attribute of that option.

For example, for the municipality of Bourscheid, the HTML looks like this:

```html
<option value="2604">Bourscheid</option>
```

In this case, the `commune_id` would be `2604`.
