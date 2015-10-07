"""
homeassistant.components.switch.rfxtrx
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Support for Rfxtrx switch.

Configuration:

To use Rfxtrx switchs you will need to add the following to your
configuration.yaml file.

switch:
  platform: rfxtrx

  devices:
    ac09c4f1: Bedroom Door
    ac09c4f2: Kitchen Door
    ac09c4f3: Bathroom Door

*Optional*

  # Automatic add new switch
  automatic_add: True

"""
import logging
import homeassistant.components.rfxtrx as rfxtrx
from RFXtrx import LightingDevice

from homeassistant.components.switch import SwitchDevice
from homeassistant.util import slugify

DEPENDENCIES = ['rfxtrx']

DOMAIN = "rfxtrx"
_LOGGER = logging.getLogger(__name__)


def setup_platform(hass, config, add_devices_callback, discovery_info=None):
    """ Setup the RFXtrx platform. """

    # Add switch from config file
    switchs = []
    devices = config.get('devices')
    if devices:
        for entity_id, entity_info in devices.items():
            if entity_id not in rfxtrx.RFX_DEVICES:
                _LOGGER.info("Add %s rfxtrx.switch", entity_info['name'])
                rfxobject = rfxtrx.get_rfx_object(entity_info['packetid'])
                newswitch = RfxtrxSwitch(entity_info['name'], rfxobject, False)
                rfxtrx.RFX_DEVICES[entity_id] = newswitch
                switchs.append(newswitch)

    add_devices_callback(switchs)

    def switch_update(event):
        """ Callback for sensor updates from the RFXtrx gateway. """
        if isinstance(event.device, LightingDevice):
            entity_id = slugify(event.device.id_string.lower())

            # Add entity if not exist and the automatic_add is True
            if entity_id not in rfxtrx.RFX_DEVICES:
                automatic_add = config.get('automatic_add', False)
                if automatic_add:
                    _LOGGER.info(
                        "Automatic add %s rfxtrx.switch (Class: %s Sub: %s)",
                        entity_id,
                        event.device.__class__.__name__,
                        event.device.subtype
                    )
                    pkt_id = "".join("{0:02x}".format(x) for x in event.data)
                    entity_name = "%s : %s" % (entity_id, pkt_id)
                    new_switch = RfxtrxSwitch(entity_name, event, False)
                    rfxtrx.RFX_DEVICES[entity_id] = new_switch
                    add_devices_callback([new_switch])

            # Check if entity exists (previous automatic added)
            if entity_id in rfxtrx.RFX_DEVICES:
                if event.values['Command'] == 'On'\
                        or event.values['Command'] == 'Off':
                    if event.values['Command'] == 'On':
                        rfxtrx.RFX_DEVICES[entity_id].turn_on()
                    else:
                        rfxtrx.RFX_DEVICES[entity_id].turn_off()

    if switch_update not in rfxtrx.RECEIVED_EVT_SUBSCRIBERS:
        rfxtrx.RECEIVED_EVT_SUBSCRIBERS.append(switch_update)


class RfxtrxSwitch(SwitchDevice):
    """ Provides a demo switch. """
    def __init__(self, name, event, state):
        self._name = name
        self._event = event
        self._state = state

    @property
    def should_poll(self):
        """ No polling needed for a demo switch. """
        return False

    @property
    def name(self):
        """ Returns the name of the device if any. """
        return self._name

    @property
    def is_on(self):
        """ True if device is on. """
        return self._state

    def turn_on(self, **kwargs):
        """ Turn the device on. """
        if self._event:
            self._event.device.send_on(rfxtrx.RFXOBJECT.transport)

        self._state = True
        self.update_ha_state()

    def turn_off(self, **kwargs):
        """ Turn the device off. """
        if self._event:
            self._event.device.send_off(rfxtrx.RFXOBJECT.transport)

        self._state = False
        self.update_ha_state()
