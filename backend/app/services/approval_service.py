from app.models.material_match import (
    MaterialMatch
)


def update_match_status(
    db,
    match_id,
    status
):

    match = db.query(
        MaterialMatch
    ).filter(
        MaterialMatch.id == match_id
    ).first()

    if not match:

        return None

    match.status = status

    db.commit()

    db.refresh(match)

    return match


def approve_match(
    db,
    match_id
):

    return update_match_status(
        db,
        match_id,
        "approved"
    )


def reject_match(
    db,
    match_id
):

    return update_match_status(
        db,
        match_id,
        "rejected"
    )