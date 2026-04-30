"""Interfaces with the SAVNO api sensors."""

import logging
from datetime import date

from homeassistant.components.sensor import SensorDeviceClass, SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from . import SavnoConfigEntry
from .const import DOMAIN
from .coordinator import SavnoCoordinator, TrashCollection

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    config_entry: SavnoConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Sensors."""
    # This gets the data update coordinator from the config entry runtime data as specified in your __init__.py
    coordinator: SavnoCoordinator = config_entry.runtime_data.coordinator

    # Enumerate all the sensors in your data value from your DataUpdateCoordinator and add an instance of your sensor class
    # to a list for each one.
    # This maybe different in your specific case, depending on how your data is structured
    sensors = [
        TrashCollectionSensor(coordinator, trash_collection)
        for trash_collection in coordinator.data.trash_collections
    ]

    # Create the sensors.
    async_add_entities(sensors)


class TrashCollectionSensor(CoordinatorEntity[SavnoCoordinator], SensorEntity):
    """Implementation of a sensor."""

    def __init__(
        self, coordinator: SavnoCoordinator, trash_data: TrashCollection
    ) -> None:
        """Initialise sensor."""
        super().__init__(coordinator)
        self.trash_data = trash_data
        self.trash_type = trash_data.trash_type
        self.istat_code = trash_data.istat_code
        self.zone = trash_data.zone

    @callback
    def _handle_coordinator_update(self) -> None:
        """Update sensor with latest data from coordinator."""
        data = self.coordinator.get_trash_collection_by_type(self.trash_type)
        if data:
            self.trash_data = data
        else:
            _LOGGER.warning("No data found for trash type %s", self.trash_type)

    @property
    def device_class(self) -> str:
        """Return device class."""
        # https://developers.home-assistant.io/docs/core/entity/sensor/#available-device-classes
        return SensorDeviceClass.DATE

    # @property
    # def device_info(self) -> DeviceInfo:
    #     """Return device information."""
    #     # Identifiers are what group entities into the same device.
    #     # If your device is created elsewhere, you can just specify the indentifiers parameter.
    #     # If your device connects via another device, add via_device parameter with the indentifiers of that device.
    #     return DeviceInfo(
    #         translation_key="n_ch_power_strip",
    #         translation_placeholders={"number_of_sockets": "2"},
    #     )

    @property
    def name(self) -> str:
        """Return the name of the sensor."""
        return self.trash_type

    @property
    def native_value(self) -> date | None:
        """Return the state of the entity."""
        if self.trash_data is not None:
            return self.trash_data.date
        return None

    @property
    def state_class(self) -> str | None:
        """Return state class."""
        # https://developers.home-assistant.io/docs/core/entity/sensor/#available-state-classes
        return None

    @property
    def unique_id(self) -> str:
        """Return unique id."""
        # All entities must have a unique id.  Think carefully what you want this to be as
        # changing it later will cause HA to create new entities.
        return f"{DOMAIN}-{self.istat_code}-{self.zone}-{self.trash_type}"

    @property
    def extra_state_attributes(self) -> dict:
        """Return the extra state attributes."""
        # Add any additional attributes you want on your sensor.
        attrs = {}
        attrs["extra_info"] = "Extra Info"
        return attrs
