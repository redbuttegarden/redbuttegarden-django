# BRAHMS batch ingestion API

Both batch routes use the existing token authentication (`Authorization: Token <token>`).
They are additive: existing single-record collection and image endpoints retain their
current request and response formats.

## Collections

`POST /plants/api/collections/bulk/` accepts JSON containing an array of no more
than 100 normal `CollectionSerializer` payloads:

```json
{
  "collections": [
    {
      "plant_id": "2026-0001*1",
      "plant_date": "2026-01-15",
      "commemoration_category": "Available",
      "commemoration_person": "",
      "species": {
        "genus": {"name": "Acer", "family": {"name": "Sapindaceae", "vernacular_name": "Soapberry"}},
        "name": "palmatum", "full_name": "Acer palmatum", "subspecies": "",
        "variety": "", "subvariety": "", "forma": "", "subforma": "", "cultivar": "",
        "vernacular_name": "Japanese maple", "habit": "Tree", "hardiness": [5, 6],
        "water_regime": "Medium", "exposure": "Part shade", "bloom_time": null,
        "plant_size": "15 feet", "flower_color": "Red", "label_range_text": "Japan",
        "utah_native": false, "plant_select": false, "deer_resist": false,
        "rabbit_resist": false, "bee_friend": false, "high_elevation": false,
        "arborist_rec": false
      },
      "location": {"latitude": "40.766367", "longitude": "-111.823807"},
      "garden": {"area": "Arboretum", "name": "Maple Walk", "code": "MW-01"}
    }
  ]
}
```

The nested fields must be the same complete fields accepted by
`POST /plants/api/collections/`. Each record preserves the established `plant_id`
upsert and nested taxonomy, location, and garden behavior. A valid envelope returns
200 and ordered `results`; each success contains `plant_id`, `created`, and the
serialized collection. Invalid records are returned as `invalid_collection` without
undoing successful records. A non-list envelope or more than 100 items returns 400.

## Images

`POST /plants/api/images/bulk/` accepts multipart form data. `manifest` is a JSON
list of no more than 20 items. Each item supplies `client_id`, `file_field`,
`copyright_info`, and exactly one target:

```json
[
  {"client_id":"plant-1", "file_field":"image_1", "copyright_info":"RBG", "plant_id":"2026-0001*1"},
  {"client_id":"species-1", "file_field":"image_2", "copyright_info":"RBG", "species":{"genus":"Acer", "name":"palmatum", "subspecies":null, "variety":null, "subvariety":null, "forma":null, "subforma":null, "cultivar":null}}
]
```

Each `file_field` names a corresponding multipart upload. Species targets must have
all eight exact taxonomy keys shown above. A syntactically invalid/non-list/oversized
manifest returns 400. Otherwise the response is always 200, in manifest order:

```json
{"results":[{"client_id":"plant-1","status":"success","created":true},{"client_id":"species-1","status":"error","code":"species_not_found","detail":"No species matches this taxonomy."}]}
```

Possible item errors include `invalid_item`, `missing_file`, `invalid_target`,
`plant_not_found`, `species_not_found`, `species_ambiguous`, `database_error`, and
`storage_error`.
Items are isolated by database savepoint. Retrying an already associated image with
the same upload filename and copyright is safe and returns `created: false`; the
existing Wagtail image, `BRAHMS Data` collection, `BRAHMS` tag, captions, and
copyright behavior are preserved.
