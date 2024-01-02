
# Frisquet Connect For Homme Assistant



## Installation

1- Copy the folder frisquet_connect into your custom_components folder
2- Restart HA and add the integration Frisquet connect from Device -> Add integration
3- Enter your Username and Password
You have now your climate Zone 1 create
Several Zones will be supported in a futur version



## Features : Frisquet vs HA logic

- HVAC Modes : Auto and Chauffe are activated. Please consider them respectively as Auto and Not Auto
- Preset Modes :
    - Réduit & Confort : Cominated with HVAC Mode Auto means you are in Auto and the preset decribes in which mode you are currently setup. Any switch between Réduit and Confort will activate a derogation mode : HVAC Mode will switch in Chauffe. This derogation will be kept until the next cycle.

    - Réduit Permanent, Confort Permanent, Hors Gel : If chosen, HVAC Mode = Chauffe. Switch back HVAC mode to Auto to stop the "Permanent" mode

    - Boost Mode : Should behave like Permanent mode : to be tested...


