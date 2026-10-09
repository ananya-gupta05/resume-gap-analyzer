import json
import re

ROLES = {
    "cloud engineer": {
        "required": ["aws", "ec2", "s3", "iam", "vpc", "linux", "docker", "git", "cloudwatch", "networking"],
        "nice": ["kubernetes", "terraform", "ci/cd", "lambda", "python", "bash", "cloudformation"],
    },
    "devops engineer": {
        "required": ["docker", "kubernetes", "ci/cd", "git", "linux", "github actions", "aws", "monitoring"],
        "nice": ["terraform", "jenkins", "prometheus", "grafana", "ansible", "helm", "bash"],
    },
    "cloud support associate": {
        "required": ["aws", "linux", "networking", "dns", "tcp/ip", "troubleshooting", "ec2", "iam"],
        "nice": ["vpc", "cloudwatch", "bash", "load balancing", "route 53"],
    },
}


def has_term(term, text):
    pattern = r"(?<![a-z0-9])" + re.escape(term) + r"(?![a-z0-9])"
    return re.search(pattern, text) is not None


def get_params(event):
    props = (
        event.get("requestBody", {})
        .get("content", {})
        .get("application/json", {})
        .get("properties", [])
    )
    return {p["name"]: p["value"] for p in props}


def respond(event, status, body):
    return {
        "messageVersion": "1.0",
        "response": {
            "actionGroup": event["actionGroup"],
            "apiPath": event["apiPath"],
            "httpMethod": event["httpMethod"],
            "httpStatusCode": status,
            "responseBody": {
                "application/json": {"body": json.dumps(body)}
            },
        },
        "sessionAttributes": event.get("sessionAttributes", {}),
        "promptSessionAttributes": event.get("promptSessionAttributes", {}),
    }


def lambda_handler(event, context):
    params = get_params(event)
    role = str(params.get("role", "")).strip().lower()
    text = str(params.get("resume_text", "")).lower()

    if role not in ROLES:
        return respond(event, 400, {
            "error": "Unknown role",
            "supported_roles": list(ROLES.keys()),
        })

    if not text.strip():
        return respond(event, 400, {"error": "resume_text is empty"})

    req = ROLES[role]["required"]
    nice = ROLES[role]["nice"]

    req_hit = [s for s in req if has_term(s, text)]
    nice_hit = [s for s in nice if has_term(s, text)]

    score = round(
        70 * len(req_hit) / len(req)
        + 30 * len(nice_hit) / len(nice)
    )

    return respond(event, 200, {
        "role": role,
        "score": score,
        "matched": req_hit + nice_hit,
        "missing_required": [s for s in req if s not in req_hit],
        "missing_nice": [s for s in nice if s not in nice_hit],
    })
