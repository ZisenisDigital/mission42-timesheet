/// <reference path="../pb_data/types.d.ts" />

/**
 * PocketBase Migration: Create Work Packages Collection
 *
 * Stores work package definitions for categorizing time blocks.
 * Work packages represent billable project categories.
 */

migrate((db) => {
  const collection = new Collection({
    "id": "work_packages_collection_id",
    "name": "work_packages",
    "type": "base",
    "system": false,
    "schema": [
      {
        "id": "work_packages_name",
        "name": "name",
        "type": "text",
        "required": true,
        "unique": true,
        "options": {
          "min": 1,
          "max": 255,
          "pattern": ""
        }
      },
      {
        "id": "work_packages_description",
        "name": "description",
        "type": "text",
        "required": false,
        "options": {
          "min": null,
          "max": 1000,
          "pattern": ""
        }
      },
      {
        "id": "work_packages_is_active",
        "name": "is_active",
        "type": "bool",
        "required": true,
        "options": {}
      },
      {
        "id": "work_packages_is_default",
        "name": "is_default",
        "type": "bool",
        "required": true,
        "options": {}
      }
    ],
    "indexes": [
      "CREATE UNIQUE INDEX idx_work_packages_name ON work_packages(name)"
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
  const collection = dao.findCollectionByNameOrId("work_packages")
  return dao.deleteCollection(collection)
})
