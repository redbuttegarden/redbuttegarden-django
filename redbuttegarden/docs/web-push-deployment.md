# Web Push deployment

1. Install the pinned dependencies, deploy the migration, and set `VAPID_PUBLIC_KEY`, `VAPID_PRIVATE_KEY`, `VAPID_CLAIMS_SUBJECT`, and `PUSH_ORIGIN_HEADER_SECRET` through the deployment secret/environment mechanism. Set the matching sensitive Terraform variable `push_origin_header_secret`; it is sent only by CloudFront to the API Gateway origin. Never put either private value in Wagtail or source control.
2. Optionally set `PUSH_ALLOWED_ENDPOINT_HOSTS` for an approved provider. Its default allows FCM, Mozilla, and Apple Web Push hosts. Set an egress policy matching this allowlist.
3. Manually append this object to each target environment's existing `events` list in `zappa_settings.json`. Do not add a second `events` key:

```json
{
  "function": "zappa_schedule.send_due_push_notifications",
  "expression": "rate(5 minutes)"
}
```

4. The Terraform deployment provisions an attached CloudFront WAF rate rule for `/push/subscriptions/` and `/push/click/`. Enable the scheduler only after the schema and environment values are live, then verify one scheduled invocation and the WAF metrics in CloudWatch.

Rollback: disable the manual scheduled event first, deploy the prior application version, and leave the additive tables in place. Rotate VAPID credentials immediately if private material is exposed.
