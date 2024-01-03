
# Frisquet Connect For Homme Assistant



## Installation

1- Copy the folder frisquet_connect into your custom_components folder<br>
2- Restart HA and add the integration Frisquet connect from Device -> Add integration<br>
3- Enter your Username and Password<br>
You have now your climate Zone 1 created<br>
Several Zones will be supported in a future version



## Features : Frisquet vs HA logic

- HVAC Modes :
    - Auto means there are no derogation. It's following Cycles Réduit & Confort that are programmed. As soon as you have a dérogation / Boost / permanent state, you are either on HVAC mode Chauffe or OFF.<br>
    - Chauffe is activated if current temperature is lower than the temprature of the derogation you have set. You should see the state chauffe is not everytime immediate as we don't take in account the temperature of the mode, but another temperature adjusted in function of mode set directly on the boiler.<br>
    - Off is set if you are in a derogated mode and current temperature is higer than the temprature of the derogation you have set<br>

The swtich to Auto will cancel any derogation.<br>
Switch to OFF or Chauffe has no effect.<br>

- Preset Modes :
    - Réduit & Confort : Cominated with HVAC Mode Auto means you are in Auto and the preset decribes in which mode you are currently setup. Any switch between Réduit and Confort will activate a derogation mode : HVAC Mode will switch in Chauffe. This derogation will be kept until the next cycle.

    - Réduit Permanent, Confort Permanent, Hors Gel : If chosen, HVAC Mode = Chauffe. Switch back HVAC mode to Auto to stop the "Permanent" mode

    - Boost Mode : Should behave like Permanent mode : to be tested...


