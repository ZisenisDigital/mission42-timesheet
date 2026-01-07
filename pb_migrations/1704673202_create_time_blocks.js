/// <reference path="../pb_data/types.d.ts" />

/**
 * PocketBase Migration: Create Time Blocks Collection
 *
 * Stores processed 30-minute time blocks after overlap resolution and auto-fill.
 * These are the final billable time entries.
 */

migrate((db) => {
  const collection = new Collection({
    "id": "time_blocks_collection_id",
    "name": "time_blocks",
    "type": "base",
    "system": false,
    "schema": [
      {
        "id": "time_blocks_week_start",
        "name": "week_start",
        "type": "date",
        "required": true,
        "options": {
          "min": "",
          "max": ""
        }
      },
      {
        "id": "time_blocks_block_start",
        "name": "block_start",
        "type": "date",
        "required": true,
        "options": {
          "min": "",
          "max": ""
        }
      },
      {
        "id": "time_blocks_block_end",
        "name": "block_end",
        "type": "date",
        "required": true,
        "options": {
          "min": "",
          "max": ""
        }
      },
      {
        "id": "time_blocks_source",
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
            "cloud_events",
            "auto_fill"
          ]
        }
      },
      {
        "id": "time_blocks_description",
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
        "id": "time_blocks_duration_hours",
        "name": "duration_hours",
        "type": "number",
        "required": true,
        "options": {
          "min": 0,
          "max": null
        }
      },
      {
        "id": "time_blocks_metadata",
        "name": "metadata",
        "type": "json",
        "required": false,
        "options": {}
      }
    ],
    "indexes": [
      "CREATE INDEX idx_time_blocks_week_start ON time_blocks(week_start)",
      "CREATE INDEX idx_time_blocks_block_start ON time_blocks(block_start)",
      "CREATE INDEX idx_time_blocks_source ON time_blocks(source)"
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
  const collection = dao.findCollectionByNameOrId("time_blocks")
  return dao.deleteCollection(collection)
})
