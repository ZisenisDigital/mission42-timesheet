/// <reference path="../pb_data/types.d.ts" />

/**
 * PocketBase Migration: Create Email Accounts Collection
 *
 * Stores Gmail account configurations for fetching sent email data.
 * Manages OAuth tokens and account-specific settings.
 */

migrate((db) => {
  const collection = new Collection({
    "id": "email_accounts_collection_id",
    "name": "email_accounts",
    "type": "base",
    "system": false,
    "schema": [
      {
        "id": "email_accounts_email",
        "name": "email",
        "type": "email",
        "required": true,
        "unique": true,
        "options": {}
      },
      {
        "id": "email_accounts_display_name",
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
        "id": "email_accounts_encrypted_token",
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
        "id": "email_accounts_is_active",
        "name": "is_active",
        "type": "bool",
        "required": true,
        "options": {}
      },
      {
        "id": "email_accounts_last_sync",
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
      "CREATE UNIQUE INDEX idx_email_accounts_email ON email_accounts(email)"
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
  const collection = dao.findCollectionByNameOrId("email_accounts")
  return dao.deleteCollection(collection)
})
