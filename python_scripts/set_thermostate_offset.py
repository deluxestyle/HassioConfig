climate = data.get('climate')
input_offset = data.get('input_offset')
offset = float(data.get('offset'))

logger.debug("offset : {}".format(offset))
logger.debug("climate : {}".format(climate))
logger.debug("input_offset : {}".format(input_offset))

# Array from 0 to 14
offset_array = 7 # = offset of 0°
offset_number = 0

if offset <= -3.5:
    offset_array = 0
    offset_number = -3.5
elif offset <= -3:
    offset_array = 1
    offset_number = -3
elif offset <= -2.5:
    offset_array = 2
    offset_number = -2.5
elif offset <= -2:
    offset_array = 3
    offset_number = -2
elif offset <= -1.5:
    offset_array = 4
    offset_number = -1.5
elif offset <= -1:
    offset_array = 5
    offset_number = -1
elif offset <= -0.5:
    offset_array = 6
    offset_number = -0.5
elif offset <= 0:
    offset_array = 7
    offset_number = 0
elif offset <= 0.5:
    offset_array = 8
    offset_number = 0.5
elif offset <= 1:
    offset_array = 9
    offset_number = 1
elif offset <= 1.5:
    offset_array = 10
    offset_number = 1.5
elif offset <= 2:
    offset_array = 11
    offset_number = 2.5
elif offset <= 2.5:
    offset_array = 12
    offset_number = 2.5
elif offset <= 3:
    offset_array = 13
    offset_number = 3
elif offset > 3:
    offset_array = 14
    offset_number = 3.5

logger.debug("offset_array : {}".format(offset_array))

# set homematic offset
if climate is not None:
    service_data = {'interface': 'rf', 'address': climate, 'paramset_key': 'MASTER', 'paramset': {'TEMPERATURE_OFFSET': offset_array} }
    logger.debug("service_data homematic: {}".format(service_data))
    hass.services.call('homematic', 'put_paramset', service_data, False)

# save current offset to input number (as a variable)
if input_offset is not None:
    service_data_input = {'entity_id': input_offset, 'value': offset_number}
    logger.debug("service_data input: {}".format(service_data_input))
    hass.services.call('input_number', 'set_value', service_data_input, False)

# interface: rf
#address: OEQ1696358
#paramset_key: MASTER
#paramset:
#  TEMPERATURE_OFFSET: 0
#homematic.put_paramset
#homeassistant.components.python_script: debug