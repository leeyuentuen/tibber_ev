import logging

from homeassistant.helpers.aiohttp_client import async_get_clientsession

from urllib3 import disable_warnings

from homeassistant.core import HomeAssistant
from homeassistant.util import Throttle


POST_HEADER_JSON = {"Content-Type": "application/json"}

_LOGGER = logging.getLogger(__name__)


class TibberEV:

    QUERY_PAYLOAD = '{"query": "{ me { homes { electricVehicles {id name shortName lastSeen lastSeenText isAlive hasNoSmartChargingCapability imgUrl schedule {isEnabled isSuspended localTimeTo minBatteryLevel} batteryText chargingText consumptionText consumptionUnitText energyCostUnitText chargeRightAwayButton chargeRightAwayAlert {imgUrl title description okText cancelText}backgroundStyle energyDealCallToAction{text url redirectUrlStartsWith link action enabled} settingsScreen{settings {key value valueType valueIsArray isReadOnly inputOptions{type title description pickerOptions {values postFix} rangeOptions{max min step defaultValue displayText displayTextPlural} selectOptions {value title description imgUrl iconName isRecommendedOption} textFieldOptions{imgUrl format placeholder} timeOptions{doNotSetATimeText}}} settingsLayout{uid type title description valueText imgUrl iconName isUpdated isEnabled callToAction {text url redirectUrlStartsWith link action enabled} childItems{uid type title description valueText imgUrl iconName isUpdated isEnabled callToAction {text url redirectUrlStartsWith link action enabled} settingKey settingKeyForIsHidden} settingKey settingKeyForIsHidden}} settingsButtonText settingsButton  {text url redirectUrlStartsWith link action enabled}enterPincode message {id title description style iconName iconSrc callToAction {text url redirectUrlStartsWith link action enabled} dismissButtonText} scheduleSuspendedText faqUrl battery { percent percentColor isCharging chargeLimit}}}}}"}'

    def __init__(self,
                 hass: HomeAssistant,
                 name: str,
                 email: str,
                 password: str) -> None:

        self.name = name
        self._status = None
        self._session = async_get_clientsession(hass, verify_ssl=False)
        self.email = email
        self.info = None
        self.id = None
        self.password = password
        self.token = None
        self.short_name = None
        self.raw_data = None
        disable_warnings()

    async def init(self):
        await self.get_token()
        self.id = "tibber_{}".format(self.name)
        if self.name is None:
            self.name = f"{self.info.identity} ({self.host})"

    async def get_token(self):
        response = await self._session.post(
            url='https://app.tibber.com/login.credentials', data={
                'email': self.email,
                'password': self.password
            },
        )
        _LOGGER.debug(f"Response {response}")
        if response.status != 200:
            _LOGGER.info("Info API not available")
            return
        resp = await response.json(content_type=None)
        self.token = resp['token']
        _LOGGER.debug(f"Response {self.token}")

    @property
    def status(self) -> str:
        return self._status

    async def async_update(self):
        response = await self._session.post(
            url='https://app.tibber.com/v4/gql',
            data=self.QUERY_PAYLOAD,
            headers={
                'authorization': f'Bearer {self.token}',
                'content-type': 'application/json'
            }
        )
        _LOGGER.debug(f"Response {response}")
        if response.status != 200:
            _LOGGER.debug("Info API not available")
            return
        resp = await response.json(content_type=None)
        _LOGGER.debug(f"Response {resp}")
        # get first raw EV data
        self.raw_data = resp['data']['me']['homes'][0]['electricVehicles'][0]
