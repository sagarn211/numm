# Service Contract

## Main backend -> AI

`POST http://localhost:8001/api/v1/match-batch`

Request:

```json
{
  "materials": [
    {
      "id": 1,
      "cpse_id": 1,
      "material_code": "ONGC-1001",
      "description": "HEX BOLT M16X50 SS304",
      "cleaned_description": "HEX BOLT M16X50 SS304",
      "category": "FASTENER",
      "unit": "EA",
      "manufacturer": null,
      "model": null,
      "specifications": {}
    }
  ]
}
```

Response:

```json
{
  "matches": [
    {
      "material_a_id": 1,
      "material_b_id": 2,
      "match_score": 0.94,
      "label": "NEAR_DUPLICATE",
      "components": {
        "semantic": 0.90,
        "attribute": 1.0,
        "fuzzy": 0.88
      },
      "attributes_a": {},
      "attributes_b": {},
      "explanation": "High similarity with matching engineering attributes.",
      "model": "all-MiniLM-L6-v2",
      "matcher_version": "1.0.0"
    }
  ]
}
```

Allowed labels:

- EXACT
- NEAR_DUPLICATE
- FUNCTIONAL_EQUIVALENT
- NO_MATCH

## Main backend -> Mock SAP

`GET http://localhost:8002/api/materials?cpse_id=1`
