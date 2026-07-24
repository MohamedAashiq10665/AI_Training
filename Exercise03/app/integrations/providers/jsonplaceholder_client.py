from app.integrations.http_client import ResilientHttpClient
from app.domain.errors import ExternalServiceError


class JsonPlaceholderActivityProvider:
    def __init__(self, client: ResilientHttpClient, bearer_token: str | None = None) -> None:
        self.client = client
        self.bearer_token = bearer_token

    def get_customer_activity(self, external_user_id: int) -> dict:
        headers: dict[str, str] = {}
        if self.bearer_token:
            headers["Authorization"] = f"Bearer {self.bearer_token}"

        todos = self.client.request_json(
            "GET",
            f"/users/{external_user_id}/todos",
            headers=headers,
        )
        posts = self.client.request_json(
            "GET",
            f"/users/{external_user_id}/posts",
            headers=headers,
        )

        if not isinstance(todos, list) or not isinstance(posts, list):
            raise ExternalServiceError("Unexpected JSONPlaceholder payload shape.")

        return {
            "open_todos": sum(1 for todo in todos if not todo.get("completed", False)),
            "total_todos": len(todos),
            "recent_post_titles": [post.get("title", "") for post in posts[:3]],
        }
