# Frisquet-connect-for-home-assistant
This repository contains the Frisquet API that can be integrated in Home Assistant.

## Features

- Create a climate entity
- Preset mode : Confort, Réduit, Hors Gel, Réduit Permanent and Boost are retrieved from the API.
- HVAC Mode : HVAC Mode is set to Auto if there is neither Dérogation active nor any Permanent mode active. If so HVAC Mode will switch to Chauffe or Off and you can revert any derogation by seting HVAC Mode to Auto

## Futur release

- Handling several zones (prepared but not tested yet because I only own 1 zone)
- Add a Device (only entity so far)
- Add a Temperature sensor Entity
- Add Water Heater entity to control Boiler