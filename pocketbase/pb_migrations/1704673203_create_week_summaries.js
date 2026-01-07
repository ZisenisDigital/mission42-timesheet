/// <reference path="../pb_data/types.d.ts" />

/**
 * PocketBase Migration: Create Week Summaries Collection
 *
 * Stores weekly summary statistics for processed time blocks.
 * Tracks total hours, auto-filled hours, and processing metadata.
 */

migrate((db) => {
  const collection = new Collection({
    "id": "week_summaries_collection_id",
    "name": "week_summaries",
    "type": "base",
    "system": false,
    "schema": [
      {
        "id": "week_summaries_week_start",
        "name": "week_start",
        "type": "date",
        "required": true,
        "unique": true,
        "options": {
          "min": "",
          "max": ""
        }
      },
      {
        "id": "week_summaries_total_hours",
        "name": "total_hours",
        "type": "number",
        "required": true,
        "options": {
          "min": 0,
          "max": null
        }
      },
      {
        "id": "week_summaries_metadata",
        "name": "metadata",
        "type": "json",
        "required": false,
        "options": {}
      }
    ],
    "indexes": [
      "CREATE UNIQUE INDEX idx_week_summaries_week_start ON week_summaries(week_start)"
    ],
    "listRule": "",
    "viewRule": "",
    "createRule": "",
    "updateRule": "",
    "deleteRule": "",
    "options": {}
  })

  return Dao(db).saveCollection(collection)
}, (db) => {
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("week_summaries")
  return dao.deleteCollection(collection)
})
