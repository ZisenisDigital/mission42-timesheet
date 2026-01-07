/// <reference path="../pb_data/types.d.ts" />

/**
 * PocketBase Migration: Create Project Specs Collection
 *
 * Stores project specification definitions for detailed time categorization.
 * Project specs provide granular breakdown within work packages.
 */

migrate((db) => {
  const collection = new Collection({
    "id": "project_specs_collection_id",
    "name": "project_specs",
    "type": "base",
    "system": false,
    "schema": [
      {
        "id": "project_specs_name",
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
        "id": "project_specs_description",
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
        "id": "project_specs_work_package",
        "name": "work_package",
        "type": "text",
        "required": false,
        "options": {
          "min": null,
          "max": 255,
          "pattern": ""
        }
      },
      {
        "id": "project_specs_is_active",
        "name": "is_active",
        "type": "bool",
        "required": true,
        "options": {}
      }
    ],
    "indexes": [
      "CREATE UNIQUE INDEX idx_project_specs_name ON project_specs(name)"
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
  const collection = dao.findCollectionByNameOrId("project_specs")
  return dao.deleteCollection(collection)
})
