climate = data.get('climate')
offset = data.get('offset')

if climate is not None:
    service_data = {'interface': 'rf', 'address': climate, 'paramset_key': 'MASTER', 'paramset': 'TEMPERATURE_OFFSET: 1' }
    hass.services.call('homematic', 'put_paramset', service_data, False)


# interface: rf
#address: OEQ1696358
#paramset_key: MASTER
#paramset:
#  TEMPERATURE_OFFSET: 0
#homematic.put_paramset