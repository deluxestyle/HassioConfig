######################################################################################
# Enable debug: setLogLevel: homeassistant.components.python_script: debug
#
# Python script um offset zu setzen
# minTemp: Falls eine kleine Temperatur eingestellt ist, soll das offset nicht gesetzt werden
######################################################################################
# set true to get only the debug values
debug = False

climate = data.get('climate')
input_offset = data.get('input_offset')
offset = float(data.get('offset'))
target_temp = float(data.get('target_temp'))
min_temp = 19

logger.debug("offset : {}".format(offset))
logger.debug("climate : {}".format(climate))
logger.debug("input_offset : {}".format(input_offset))

# Array from 0 to 14
offset_array = 7 # = offset of 0°
offset_number = 0

# Homematic does not accept temparatures lower than -3.5 or higher than 3.5
offsetTmp = round(offset, 0) / 2
if offsetTmp < -3.5:
    offsetTmp = -3.5
if offsetTmp > 3.5:
    offsetTmp = 3.5

# Now we calculate the Homematic value, the rule is as follows:
# -3,5° | -3,0° | -2,5° | -2,0° | -1,5° | -1,0° | -0,5° | 0,0° | +0,5° | +1,0° | +1,5° | +2,0° | +2,5° | +3,0° | +3,5°
offset_array = int((offsetTmp * 2) + 7)
offset_number = offsetTmp

logger.debug("offset_array : {}".format(offset_array))
logger.debug("offset_number : {}".format(offset_number))

if target_temp < min_temp or debug:
    if debug:
        logger.debug("Nur zu debug Zwecken")
    else:
        logger.debug("Kein Offset, da Temperatur zu niedrig")
else:
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