"""Listing 2a from the paper — default vacuum cleaner behaviour."""

# Simple on/off toggle with click event
DEFAULT_PROGRAM = """\
states
  on  = turn-on
  off = turn-off
events
  click = get.click()
transitions
  on  { click => off }
  off { click => on  }
"""
