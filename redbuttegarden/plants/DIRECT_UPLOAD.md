# BRAHMS direct S3 image uploads

Use this two-phase API when image bytes must bypass API Gateway and Lambda. Both endpoints require the existing DRF token authentication.

## Initiate

`POST /plants/api/images/direct-upload/initiate/` accepts JSON with at most 20 `uploads`. Each upload supplies a string `client_id`, `copyright_info`, exactly one `plant_id` or complete `species` taxonomy target, plus `original_filename`, `content_type`, `byte_size`, positive `image_width`/`image_height`, and lowercase hexadecimal `sha256`. Dimensions are required so Wagtail can register the server-side-copied object without Lambda reopening image bytes; their product is bounded by `WAGTAILIMAGES_MAX_IMAGE_PIXELS`.

```json
{
  "uploads": [{
    "client_id": "plant-photo-1",
    "plant_id": "2026-0400*1",
    "copyright_info": "Red Butte Garden",
    "original_filename": "garden-plant.jpg",
    "content_type": "image/jpeg",
    "byte_size": 22144,
    "image_width": 1200,
    "image_height": 800,
    "sha256": "0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef"
  }]
}
```

Each successful result returns a server-generated `pending_id`, opaque staging key, 24-hour pending expiry, and a 15-minute S3 presigned POST (`upload.url` and `upload.fields`). Submit the returned fields and bytes directly to S3 without changing the exact key, content type, declared size, SHA-256 metadata/checksum, dimension metadata, or `AES256` encryption field. The authenticated BRAHMS CLI must derive the declared dimensions from the actual image before initiating; finalization verifies the signed S3 metadata but deliberately does not read image bytes through Lambda.

## Finalize

`POST /plants/api/images/direct-upload/finalize/` accepts at most 20 `uploads`, each containing exactly one `pending_id` or `client_id`.

```json
{"uploads": [{"pending_id": "c9b96029-bd99-42ca-943e-f93c2201b9b2"}]}
```

The server checks ownership, expiration, S3 object existence, content type, byte size, SHA-256 and dimension metadata/checksum, and encryption. It then copies the object server-side into Wagtail media and applies the same title-based Wagtail/BRAHMS association behavior as the existing endpoints. A repeated finalized request returns the original success outcome and creates no duplicate image or association while its pending record is retained. All pending and finalized outcome rows expire 24 hours after initiation; callers should therefore retry finalization within that window. Finalized staging objects are deleted; unfinalized `brahms-staging/` objects expire after 24 hours. If a later Wagtail database or relationship operation fails after the server-side copy, the destination copy is deleted.

## Deployment requirements

The application derives the runtime bucket and `media/` prefix from the active Wagtail `MediaStorage`; it never accepts a client object key. Terraform requires the existing private media bucket and Zappa role names via `wagtail_media_bucket_name` and `zappa_execution_role_name`. It attaches only staging `PutObject`/`GetObject`/`DeleteObject` permissions and destination-media `PutObject`/`DeleteObject` permissions for the copied-object rollback. Do not add staging objects to CloudFront or a public bucket policy, and do not add browser CORS for this CLI workflow.

The deployed media bucket is owned outside this Terraform state. Its owner must merge the required one-day `brahms-staging/` expiry rule from [`terraform/brahms-staging-lifecycle-rule.json`](../terraform/brahms-staging-lifecycle-rule.json) into that bucket's existing lifecycle configuration before enabling direct uploads. Do not manage this externally owned bucket with a standalone Terraform `aws_s3_bucket_lifecycle_configuration` resource: that resource replaces the bucket's complete lifecycle configuration and could remove unrelated rules.

Schedule `python manage.py purge_expired_brahms_uploads` at least daily in the deployment-owned, ignored `zappa_settings.json`; S3 lifecycle can remove objects but cannot delete the 24-hour database outcome rows.
