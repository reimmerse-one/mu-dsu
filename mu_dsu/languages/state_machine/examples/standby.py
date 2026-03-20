"""Listing 2b from the paper — extended behaviour with stand-by."""

# Stand-by mode: vacuum turns off after inactivity
STANDBY_PROGRAM = """\
counter t
states
  on       = turn-on ; t <- 0
  off      = turn-off
  stand-by = t <- t + 1
events
  click      = get.click()
  elapsed    = t > 10
  activity   = get.activity()
  inactivity = get.time()
transitions
  on  { click => off ; inactivity => stand-by }
  off { click => on }
  stand-by { click => off ; elapsed => off ; inactivity => stand-by ; activity => on }
"""
