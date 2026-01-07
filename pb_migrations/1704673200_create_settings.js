/// <reference path="../pb_data/types.d.ts" />

/**
 * PocketBase Migration: Create Settings Collection
 *
 * This migration creates the settings collection for storing all configuration
 * parameters for the Mission42 Timesheet system.
 *
 * Settings are stored as key-value pairs with:
 * - key: unique identifier (e.g., "work_week_start_day")
 * - value: stored as text (parsed based on type field)
 * - type: data type (string, number, boolean)
 * - category: grouping for admin UI
 * - description: human-readable explanation
 * - validation_rules: JSON with validation constraints
 */

migrate((db) => {
  const collection = new Collection({
    "id": "settings_collection_id",
    "name": "settings",
    "type": "base",
    "system": false,
    "schema": [
      {
        "id": "settings_key",
        "name": "key",
        "type": "text",
        "required": true,
        "unique": true,
        "options": {
          "min": 1,
          "max": 100,
          "pattern": ""
        }
      },
      {
        "id": "settings_value",
        "name": "value",
        "type": "text",
        "required": true,
        "options": {
          "min": null,
          "max": 1000,
          "pattern": ""
        }
      },
      {
        "id": "settings_type",
        "name": "type",
        "type": "select",
        "required": true,
        "options": {
          "maxSelect": 1,
          "values": [
            "string",
            "number",
            "boolean"
          ]
        }
      },
      {
        "id": "settings_description",
        "name": "description",
        "type": "text",
        "required": false,
        "options": {
          "min": null,
          "max": 500,
          "pattern": ""
        }
      },
      {
        "id": "settings_category",
        "name": "category",
        "type": "select",
        "required": true,
        "options": {
          "maxSelect": 1,
          "values": [
            "core",
            "wakatime",
            "calendar",
            "gmail",
            "github",
            "cloud_events",
            "processing",
            "export"
          ]
        }
      },
      {
        "id": "settings_validation_rules",
        "name": "validation_rules",
        "type": "json",
        "required": false,
        "options": {}
      }
    ],
    "indexes": [
      "CREATE UNIQUE INDEX idx_settings_key ON settings(key)",
      "CREATE INDEX idx_settings_category ON settings(category)"
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
  // Rollback: delete settings collection
  const dao = new Dao(db)
  const collection = dao.findCollectionByNameOrId("settings")

  return dao.deleteCollection(collection)
})
