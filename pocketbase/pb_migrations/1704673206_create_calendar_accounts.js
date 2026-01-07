/// <reference path="../pb_data/types.d.ts" />

/**
 * PocketBase Migration: Create Calendar Accounts Collection
 *
 * Stores Google Calendar account configurations for fetching meeting data.
 * Manages OAuth tokens and monitored calendar settings.
 */

migrate((db) => {
  const collection = new Collection({
    "id": "calendar_accounts_collection_id",
    "name": "calendar_accounts",
    "type": "base",
    "system": false,
    "schema": [
      {
        "id": "calendar_accounts_email",
        "name": "email",
        "type": "email",
        "required": true,
        "unique": true,
        "options": {}
      },
      {
        "id": "calendar_accounts_display_name",
        "name": "display_name",
        "type": "text",
        "required": false,
        "options": {
          "min": null,
          "max": 255,
          "pattern": ""
        }
      },
      {
        "id": "calendar_accounts_calendar_id",
        "name": "calendar_id",
        "type": "text",
        "required": false,
        "options": {
          "min": null,
          "max": 255,
          "pattern": ""
        }
      },
      {
        "id": "calendar_accounts_encrypted_token",
        "name": "encrypted_token",
        "type": "text",
        "required": false,
        "options": {
          "min": null,
          "max": 10000,
          "pattern": ""
        }
      },
      {
        "id": "calendar_accounts_is_active",
        "name": "is_active",
        "type": "bool",
        "required": true,
        "options": {}
      },
      {
        "id": "calendar_accounts_last_sync",
        "name": "last_sync",
        "type": "date",
        "required": false,
        "options": {
          "min": "",
          "max": ""
        }
      }
    ],
    "indexes": [
      "CREATE UNIQUE INDEX idx_calendar_accounts_email ON calendar_accounts(email)"
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
  const collection = dao.findCollectionByNameOrId("calendar_accounts")
  return dao.deleteCollection(collection)
})
