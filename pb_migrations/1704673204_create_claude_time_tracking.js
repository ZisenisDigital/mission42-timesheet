/// <reference path="../pb_data/types.d.ts" />

/**
 * PocketBase Migration: Create Claude Time Tracking Collection
 *
 * Stores Claude Code AI assistant usage data for time tracking.
 * Tracks sessions, tools used, project context, and duration.
 */

migrate((db) => {
  const collection = new Collection({
    "id": "claude_time_tracking_collection_id",
    "name": "claude_time_tracking",
    "type": "base",
    "system": false,
    "schema": [
      {
        "id": "claude_time_tracking_session_id",
        "name": "session_id",
        "type": "text",
        "required": true,
        "options": {
          "min": 1,
          "max": 255,
          "pattern": ""
        }
      },
      {
        "id": "claude_time_tracking_tool_name",
        "name": "tool_name",
        "type": "text",
        "required": false,
        "options": {
          "min": null,
          "max": 255,
          "pattern": ""
        }
      },
      {
        "id": "claude_time_tracking_description",
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
        "id": "claude_time_tracking_started_at",
        "name": "started_at",
        "type": "date",
        "required": true,
        "options": {
          "min": "",
          "max": ""
        }
      },
      {
        "id": "claude_time_tracking_completed_at",
        "name": "completed_at",
        "type": "date",
        "required": false,
        "options": {
          "min": "",
          "max": ""
        }
      },
      {
        "id": "claude_time_tracking_duration",
        "name": "duration",
        "type": "number",
        "required": false,
        "options": {
          "min": 0,
          "max": null
        }
      },
      {
        "id": "claude_time_tracking_status",
        "name": "status",
        "type": "text",
        "required": false,
        "options": {
          "min": null,
          "max": 50,
          "pattern": ""
        }
      },
      {
        "id": "claude_time_tracking_topic",
        "name": "topic",
        "type": "text",
        "required": false,
        "options": {
          "min": null,
          "max": 255,
          "pattern": ""
        }
      },
      {
        "id": "claude_time_tracking_project",
        "name": "project",
        "type": "text",
        "required": false,
        "options": {
          "min": null,
          "max": 255,
          "pattern": ""
        }
      }
    ],
    "indexes": [
      "CREATE INDEX idx_claude_time_tracking_started_at ON claude_time_tracking(started_at)",
      "CREATE INDEX idx_claude_time_tracking_project ON claude_time_tracking(project)"
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
  const collection = dao.findCollectionByNameOrId("claude_time_tracking")
  return dao.deleteCollection(collection)
})
