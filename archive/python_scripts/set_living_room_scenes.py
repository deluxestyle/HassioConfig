group_entities = hass.states.get('group.scenes_living_room').attributes['entity_id']
all_scenes = []
all_scenes.append("--")
for e in group_entities:
    all_scenes.append(hass.states.get(e).attributes['friendly_name'].replace("Wohnzimmer ", ""))
service_data = {'entity_id': 'input_select.scenes_living_room',
                'options': all_scenes}
hass.services.call('input_select', 'set_options', service_data)