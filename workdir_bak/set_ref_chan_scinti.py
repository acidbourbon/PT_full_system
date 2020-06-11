#!/usr/bin/env python3

import db


setup = db.get_setup_json()
setup["global_settings"]["reference_channel"] = 35131
db.write_setup_json(setup)
