for notif in hass.states.entity_ids('persistent_notification'):
    hass.services.call(
        'persistent_notification', 'dismiss',
        {"notification_id": notif.split('.', 1)[-1]})