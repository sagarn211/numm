import math
def paginate(query, page: int, limit: int):
    page = max(page, 1)
    limit = min(max(limit, 1), 100)
    total = query.count()
    return {
        "items": query.offset((page - 1) * limit).limit(limit).all(),
        "page": page,
        "limit": limit,
        "total": total,
        "pages": math.ceil(total / limit) if total else 0,
    }
