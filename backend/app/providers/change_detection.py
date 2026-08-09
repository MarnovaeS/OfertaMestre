from app.providers.contracts import CatalogItem


def has_app_changed(previous: CatalogItem | None, current: CatalogItem) -> bool:
    if previous is None:
        return True
    return (
        previous.last_modified != current.last_modified
        or previous.price_change_number != current.price_change_number
        or previous.name != current.name
    )
