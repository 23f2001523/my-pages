import uuid


def get_request_id(request):

    rid = request.headers.get("X-Request-ID")

    if rid:
        return rid

    return str(uuid.uuid4())
