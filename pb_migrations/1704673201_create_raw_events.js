/// <reference path="../pb_data/types.d.ts" />

/**
 * PocketBase Migration: Create Raw Events Collection
 *
 * Stores raw events from all data sources before processing into time blocks.
 * Events are fetched from WakaTime, Calendar, Gmail, GitHub, and Cloud Events.
 */

migrate((db) => {
  const collection = new Collection({
    "id": "raw_events_collection_id",
    "name": "raw_events",
    "type": "base",
    "system": false,
    "schema": [
      {
        "id": "raw_events_source",
        "name": "source",
        "type": "select",
        "required": true,
        "options": {
          "maxSelect": 1,
          "values": [
            "wakatime",
            "calendar",
            "gmail",
            "github",
            "cloud_events"
          ]
        }
      },
      {
        "id": "raw_events_source_id",
        "name": "source_id",
        "type": "text",
        "required": true,
        "options": {
          "min": 1,
          "max": 255,
          "pattern": ""
        }
      },
      {
        "id": "raw_events_timestamp",
        "name": "timestamp",
        "type": "date",
        "required": true,
        "options": {
          "min": "",
          "max": ""
        }
      },
      {
        "id": "raw_events_duration_minutes",
        "name": "duration_minutes",
        "type": "number",
        "required": true,
        "options": {
          "min": 0,
          "max": null
        }
      },
      {
        "id": "raw_events_description",
        "name": "description",
        "type": "text",
        "required": true,
        "options": {
          "min": 1,
          "max": 1000,
          "pattern": ""
        }
      },
      {
        "id": "raw_events_metadata",
        "name": "metadata",
        "type": "json",
        "required": false,
        "options": {}
      }
    ],
    "indexes": [
      "CREATE UNIQUE INDEX idx_raw_events_source_id ON raw_events(source, source_id)",
      "CREATE INDEX idx_raw_events_timestamp ON raw_events(timestamp)",
      "CREATE INDEX idx_raw_events_source ON raw_events(source)"
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
  const collection = dao.findCollectionByNameOrId("raw_events")
  return dao.deleteCollection(collection)
})
