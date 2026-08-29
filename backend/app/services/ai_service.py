import httpx

from app.config.settings import settings


async def get_ai_matches(
    materials
):

    url = (
        f"{settings.AI_SERVICE_URL}"
        "/api/matching"
    )

    payload = {
        "materials": materials
    }

    async with httpx.AsyncClient(
        timeout=60
    ) as client:

        response = await client.post(
            url,
            json=payload
        )

        response.raise_for_status()

        return response.json()